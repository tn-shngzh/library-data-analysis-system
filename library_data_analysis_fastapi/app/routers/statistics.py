import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timedelta
from typing import Optional
import numpy as np
from scipy import stats as scipy_stats
from app.database import run_sync_db
from app.cache import cache
from app.auth import get_current_user

router = APIRouter(prefix="/api/stats", tags=["统计分析"])
logger = logging.getLogger(__name__)


def _calc_frequency_stats(counts):
    if not counts:
        return {"count": 0, "mean": 0, "std": 0, "min": 0, "max": 0, "q25": 0, "median": 0, "q75": 0}
    arr = np.array(counts)
    return {
        "count": len(counts),
        "mean": round(float(np.mean(arr)), 2),
        "std": round(float(np.std(arr)), 2),
        "min": int(np.min(arr)),
        "max": int(np.max(arr)),
        "q25": int(np.percentile(arr, 25)),
        "median": int(np.median(arr)),
        "q75": int(np.percentile(arr, 75))
    }


@router.get("/frequency")
async def get_frequency_analysis(
    type: str = Query("book", description="分析类型: book(图书借阅频次), reader(读者借阅频次), category(分类频次), action(操作类型频次)"),
    year: Optional[int] = None,
    current_user=Depends(get_current_user)
):
    cache_key = f"stats:frequency:{type}:{year}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        def _query(conn):
            today = datetime.now().date()
            with conn.cursor() as cur:
                cur.execute("SELECT MAX(borrow_date) FROM circulations")
                row = cur.fetchone()
                current_year = (row[0] // 10000) if row and row[0] else today.year
                
                if year is None:
                    year = current_year

                if year != today.year:
                    start = int(f"{year}0101")
                    end = int(f"{year}1231")
                else:
                    start = int(f"{today.year}0101")
                    end = int(today.strftime('%Y%m%d'))

                if type == "book":
                    cur.execute("""
                        SELECT bib_id, COUNT(*) as borrow_count
                        FROM circulations
                        WHERE borrow_date BETWEEN %s AND %s AND status = 'borrowed'
                        GROUP BY bib_id
                        ORDER BY borrow_count DESC
                    """, (start, end))
                    rows = cur.fetchall()
                    counts = [r[1] for r in rows]
                    if counts:
                        max_val = max(counts)
                        bins = list(range(0, max_val + 2))
                        hist, _ = np.histogram(counts, bins=bins)
                    else:
                        hist = np.array([0, 0, 0])
                    return {
                        "type": "book",
                        "title": "图书借阅频次分布",
                        "description": "统计每本图书被借阅的次数分布",
                        "distribution": {
                            "bins": list(range(0, len(hist))),
                            "frequencies": hist.tolist()
                        },
                        "summary": _calc_frequency_stats(counts)
                    }

                elif type == "reader":
                    cur.execute("""
                        SELECT borrower_id, COUNT(*) as borrow_count
                        FROM circulations
                        WHERE borrow_date BETWEEN %s AND %s AND status = 'borrowed'
                        GROUP BY borrower_id
                    """, (start, end))
                    rows = cur.fetchall()
                    counts = [r[1] for r in rows]
                    max_val = max(counts) if counts else 10
                    bins = list(range(0, min(max_val + 2, 51)))
                    hist, _ = np.histogram(counts, bins=bins)
                    return {
                        "type": "reader",
                        "title": "读者借阅频次分布",
                        "description": "统计每位读者的借阅次数分布",
                        "distribution": {
                            "bins": list(range(0, len(hist))),
                            "frequencies": hist.tolist()
                        },
                        "summary": _calc_frequency_stats(counts)
                    }

                elif type == "category":
                    cur.execute("""
                        SELECT bc.category, COUNT(*) as count
                        FROM circulations c
                        JOIN book_categories bc ON c.bib_id = bc.bib_id
                        WHERE c.borrow_date BETWEEN %s AND %s
                        GROUP BY bc.category
                        ORDER BY count DESC
                    """, (start, end))
                    rows = cur.fetchall()
                    total = sum(r[1] for r in rows)
                    return {
                        "type": "category",
                        "title": "图书分类频次分布",
                        "description": "各分类借阅次数占比",
                        "distribution": [
                            {"category": r[0], "count": r[1], "percent": round(r[1] / total * 100, 2) if total > 0 else 0}
                            for r in rows
                        ],
                        "summary": {"total": total, "categories": len(rows)}
                    }

                elif type == "action":
                    cur.execute("""
                        SELECT status, COUNT(*) as count
                        FROM circulations
                        WHERE borrow_date BETWEEN %s AND %s
                        GROUP BY status
                        ORDER BY count DESC
                    """, (start, end))
                    rows = cur.fetchall()
                    total = sum(r[1] for r in rows)
                    action_names = {'borrowed': '借出', 'returned': '归还'}
                    return {
                        "type": "action",
                        "title": "操作类型频次分布",
                        "description": "各类操作的次数占比",
                        "distribution": [
                            {"action": r[0], "name": action_names.get(r[0], r[0]), "count": r[1], "percent": round(r[1] / total * 100, 2) if total > 0 else 0}
                            for r in rows
                        ],
                        "summary": {"total": total, "actions": len(rows)}
                    }
                
                return {"error": "不支持的分析类型"}

        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取频数分析失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取频数分析失败: {e}")


@router.get("/descriptive")
async def get_descriptive_stats(
    type: str = Query("borrows", description="类型: borrows(借阅量), readers(读者活跃), returns(归还量)"),
    year: Optional[int] = None,
    period: str = Query("monthly", description="周期: daily, monthly, weekly"),
    current_user=Depends(get_current_user)
):
    cache_key = f"stats:descriptive:{type}:{year}:{period}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        def _query(conn):
            today = datetime.now().date()
            with conn.cursor() as cur:
                cur.execute("SELECT MAX(borrow_date) FROM circulations")
                row = cur.fetchone()
                current_year = (row[0] // 10000) if row and row[0] else today.year
                
                if year is None:
                    year = current_year

                if year != today.year:
                    start = int(f"{year}0101")
                    end = int(f"{year}1231")
                else:
                    start = int(f"{today.year}0101")
                    end = int(today.strftime('%Y%m%d'))

                if period == "daily":
                    group_expr = "borrow_date"
                elif period == "weekly":
                    group_expr = "(borrow_date - 20200101) / 7"
                else:
                    group_expr = "borrow_date / 100"

                if type == "borrows":
                    cur.execute("""
                        SELECT %s, COUNT(*) as count
                        FROM circulations
                        WHERE borrow_date BETWEEN %%s AND %%s AND status = 'borrowed'
                        GROUP BY %s
                        ORDER BY 1
                    """ % (group_expr, group_expr), (start, end))
                    rows = cur.fetchall()
                elif type == "returns":
                    cur.execute("""
                        SELECT %s, COUNT(*) as count
                        FROM circulations
                        WHERE borrow_date BETWEEN %%s AND %%s AND status = 'returned'
                        GROUP BY %s
                        ORDER BY 1
                    """ % (group_expr, group_expr), (start, end))
                    rows = cur.fetchall()
                else:
                    cur.execute("""
                        SELECT %s, COUNT(DISTINCT borrower_id) as count
                        FROM circulations
                        WHERE borrow_date BETWEEN %%s AND %%s
                        GROUP BY %s
                        ORDER BY 1
                    """ % (group_expr, group_expr), (start, end))
                    rows = cur.fetchall()

                if not rows:
                    return {"type": type, "title": f"{type}描述性统计", "data": [], "stats": {}}

                counts = [r[1] for r in rows]
                arr = np.array(counts)
                labels = [str(r[0]) for r in rows]

                return {
                    "type": type,
                    "title": f"{type}描述性统计",
                    "data": [{"date": labels[i], "value": counts[i]} for i in range(len(rows))],
                    "stats": {
                        "count": len(counts),
                        "sum": int(np.sum(arr)),
                        "mean": round(float(np.mean(arr)), 2),
                        "std": round(float(np.std(arr)), 2),
                        "min": int(np.min(arr)),
                        "max": int(np.max(arr)),
                        "q25": round(float(np.percentile(arr, 25)), 2),
                        "median": round(float(np.median(arr)), 2),
                        "q75": round(float(np.percentile(arr, 75)), 2),
                        "skewness": round(float(scipy_stats.skew(arr)), 3),
                        "kurtosis": round(float(scipy_stats.kurtosis(arr)), 3)
                    }
                }

        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取描述性统计失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取描述性统计失败: {e}")


@router.get("/crosstab")
async def get_cross_tabulation(
    row: str = Query("category", description="行维度: category(分类), degree(学历), action(操作类型)"),
    col: str = Query("action", description="列维度: action(操作类型), month(月份)"),
    year: Optional[int] = None,
    current_user=Depends(get_current_user)
):
    cache_key = f"stats:crosstab:{row}:{col}:{year}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        def _query(conn):
            today = datetime.now().date()
            with conn.cursor() as cur:
                cur.execute("SELECT MAX(borrow_date) FROM circulations")
                row_db = cur.fetchone()
                current_year = (row_db[0] // 10000) if row_db and row_db[0] else today.year
                
                if year is None:
                    year = current_year

                if year != today.year:
                    start = int(f"{year}0101")
                    end = int(f"{year}1231")
                else:
                    start = int(f"{today.year}0101")
                    end = int(today.strftime('%Y%m%d'))

                action_names = {'CKO': '借出', 'CKI': '归还', 'REH': '馆内续借', 'REI': '线上续借'}

                if row == "category" and col == "action":
                    cur.execute("""
                        SELECT bc.category, c.status, COUNT(*) as count
                        FROM circulations c
                        JOIN book_categories bc ON c.bib_id = bc.bib_id
                        WHERE c.borrow_date BETWEEN %s AND %s
                        GROUP BY bc.category, c.status
                        ORDER BY bc.category, count DESC
                    """, (start, end))
                elif row == "degree" and col == "action":
                    cur.execute("""
                        SELECT b.degree, c.status, COUNT(*) as count
                        FROM circulations c
                        JOIN borrowers b ON c.borrower_id = b.id
                        WHERE c.borrow_date BETWEEN %s AND %s
                        GROUP BY b.degree, c.status
                        ORDER BY b.degree, count DESC
                    """, (start, end))
                elif row == "category" and col == "month":
                    cur.execute("""
                        SELECT bc.category,
                               MOD(c.borrow_date, 10000) / 100 as month,
                               COUNT(*) as count
                        FROM circulations c
                        JOIN book_categories bc ON c.bib_id = bc.bib_id
                        WHERE c.borrow_date BETWEEN %s AND %s
                        GROUP BY bc.category, month
                        ORDER BY bc.category, month
                    """, (start, end))
                    action_names = {i: f"{i}月" for i in range(1, 13)}
                else:
                    return {"error": "不支持的组合", "data": [], "rowHeaders": [], "colHeaders": [], "matrix": []}

                rows = cur.fetchall()
                if not rows:
                    return {"data": [], "rowHeaders": [], "colHeaders": [], "matrix": []}

                row_keys = sorted(set(r[0] for r in rows))
                col_keys = sorted(set(r[1] for r in rows))
                matrix = []
                for rk in row_keys:
                    row_data = []
                    for ck in col_keys:
                        count = next((r[2] for r in rows if r[0] == rk and r[1] == ck), 0)
                        row_data.append(count)
                    matrix.append(row_data)

                total_row = []
                for j in range(len(col_keys)):
                    total_row.append(sum(matrix[i][j] for i in range(len(row_keys))))
                matrix.append(total_row)

                return {
                    "rowHeaders": row_keys + ["总计"],
                    "colHeaders": [action_names.get(k, str(k)) for k in col_keys],
                    "matrix": matrix,
                    "rowLabel": row,
                    "colLabel": col
                }

        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取交叉表失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取交叉表失败: {e}")


@router.get("/correlation-matrix")
async def get_correlation_matrix(
    year: Optional[int] = None,
    current_user=Depends(get_current_user)
):
    cache_key = f"stats:correlation:{year}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        def _query(conn):
            today = datetime.now().date()
            with conn.cursor() as cur:
                cur.execute("SELECT MAX(borrow_date) FROM circulations")
                row = cur.fetchone()
                current_year = (row[0] // 10000) if row and row[0] else today.year
                
                if year is None:
                    year = current_year

                if year != today.year:
                    start = int(f"{year}0101")
                    end = int(f"{year}1231")
                else:
                    start = int(f"{today.year}0101")
                    end = int(today.strftime('%Y%m%d'))

                cur.execute("""
                    SELECT b.degree, bc.category,
                           COUNT(CASE WHEN c.status = 'borrowed' THEN 1 END) as borrowed,
                           COUNT(CASE WHEN c.status = 'returned' THEN 1 END) as returned,
                           COUNT(DISTINCT c.borrower_id) as readers
                    FROM circulations c
                    JOIN borrowers b ON c.borrower_id = b.id
                    JOIN book_categories bc ON c.bib_id = bc.bib_id
                    WHERE c.borrow_date BETWEEN %s AND %s
                    GROUP BY b.degree, bc.category
                """, (start, end))
                rows = cur.fetchall()

                degrees = sorted(set(r[0] for r in rows))
                categories = sorted(set(r[1] for r in rows))

                borrowed_matrix = []
                for deg in degrees:
                    row_data = []
                    for cat in categories:
                        val = next((r[2] for r in rows if r[0] == deg and r[1] == cat), 0)
                        row_data.append(val)
                    borrowed_matrix.append(row_data)

                corr_matrix = []
                for i, deg1 in enumerate(degrees):
                    row_data = []
                    for j, deg2 in enumerate(degrees):
                        if i == j:
                            row_data.append(1.0)
                        else:
                            vec1 = np.array(borrowed_matrix[i])
                            vec2 = np.array(borrowed_matrix[j])
                            if np.std(vec1) > 0 and np.std(vec2) > 0:
                                corr = np.corrcoef(vec1, vec2)[0, 1]
                                row_data.append(round(float(corr), 3) if not np.isnan(corr) else 0)
                            else:
                                row_data.append(0)
                    corr_matrix.append(row_data)

                return {
                    "variables": degrees,
                    "matrix": corr_matrix,
                    "type": "pearson"
                }

        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取相关性矩阵失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取相关性矩阵失败: {e}")


@router.get("/clustering/reader")
async def get_reader_clustering(
    year: Optional[int] = None,
    n_clusters: int = Query(4, ge=2, le=8, description="聚类数量"),
    current_user=Depends(get_current_user)
):
    cache_key = f"stats:clustering:reader:{year}:{n_clusters}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        def _query(conn):
            today = datetime.now().date()
            with conn.cursor() as cur:
                cur.execute("SELECT MAX(borrow_date) FROM circulations")
                row = cur.fetchone()
                current_year = (row[0] // 10000) if row and row[0] else today.year
                
                if year is None:
                    year = current_year

                if year != today.year:
                    start = int(f"{year}0101")
                    end = int(f"{year}1231")
                else:
                    start = int(f"{today.year}0101")
                    end = int(today.strftime('%Y%m%d'))

                cur.execute("""
                    SELECT borrower_id,
                           COUNT(*) as total_actions,
                           COUNT(CASE WHEN status = 'borrowed' THEN 1 END) as borrows,
                           COUNT(CASE WHEN status = 'returned' THEN 1 END) as returns,
                           COUNT(DISTINCT bib_id) as unique_books
                    FROM circulations
                    WHERE borrow_date BETWEEN %s AND %s
                    GROUP BY borrower_id
                    HAVING COUNT(*) >= 5
                    LIMIT 1000
                """, (start, end))
                rows = cur.fetchall()

                if len(rows) < n_clusters:
                    return {"error": f"样本量({len(rows)})少于聚类数({n_clusters})", "clusters": []}

                features = np.array([[r[1], r[2], r[3], r[4]] for r in rows])
                features_scaled = (features - features.mean(axis=0)) / (features.std(axis=0) + 1e-8)

                from scipy.cluster.vq import kmeans2
                centroids, labels = kmeans2(features_scaled, n_clusters, minit='++')

                cluster_stats = {}
                for i, label in enumerate(labels):
                    if label not in cluster_stats:
                        cluster_stats[label] = {"count": 0, "total": [], "borrows": [], "returns": [], "books": []}
                    cluster_stats[label]["count"] += 1
                    cluster_stats[label]["total"].append(rows[i][1])
                    cluster_stats[label]["borrows"].append(rows[i][2])
                    cluster_stats[label]["returns"].append(rows[i][3])
                    cluster_stats[label]["books"].append(rows[i][4])

                clusters = []
                for label, stats in cluster_stats.items():
                    avg_borrows = np.mean(stats["borrows"])
                    avg_returns = np.mean(stats["returns"])
                    ratio = avg_borrows / avg_returns if avg_returns > 0 else 0

                    if avg_borrows > np.mean(features[:, 1]) * 1.5:
                        name = "高频借阅型"
                    elif abs(ratio - 1) < 0.2:
                        name = "均衡借还型"
                    elif ratio > 1.3:
                        name = "借多还少型"
                    else:
                        name = "低频沉默型"

                    clusters.append({
                        "id": int(label),
                        "name": name,
                        "count": stats["count"],
                        "percent": round(stats["count"] / len(rows) * 100, 1),
                        "avg_borrows": round(float(np.mean(stats["borrows"])), 1),
                        "avg_returns": round(float(np.mean(stats["returns"])), 1),
                        "avg_unique_books": round(float(np.mean(stats["books"])), 1),
                        "centroid": centroids[label].tolist()
                    })

                clusters = sorted(clusters, key=lambda x: x["count"], reverse=True)
                for i, c in enumerate(clusters):
                    c["id"] = i

                return {
                    "clusters": clusters,
                    "summary": {
                        "total_readers": len(rows),
                        "n_clusters": n_clusters
                    }
                }

        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 600)
        return result
    except Exception as e:
        logger.error("获取读者聚类失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取聚类分析失败: {e}")


@router.get("/regression/forecast")
async def get_borrow_forecast(
    forecast_days: int = Query(30, ge=7, le=90, description="预测天数"),
    current_user=Depends(get_current_user)
):
    today = datetime.now().date()
    today_int = int(today.strftime('%Y%m%d'))
    start_date = int((today - timedelta(days=365)).strftime('%Y%m%d'))

    cache_key = f"stats:regression:forecast:{forecast_days}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        def _query(conn):
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT borrow_date, COUNT(*) as count
                    FROM circulations
                    WHERE borrow_date BETWEEN %s AND %s
                    GROUP BY borrow_date
                    ORDER BY borrow_date
                """, (start_date, today_int))
                rows = cur.fetchall()

                if len(rows) < 30:
                    return {"error": "历史数据不足，无法进行预测", "forecast": []}

                dates = [(today - timedelta(days=len(rows) - 1 - i)).strftime('%Y-%m-%d') for i in range(len(rows))]
                counts = [r[1] for r in rows]

                X = np.arange(len(counts)).reshape(-1, 1)
                y = np.array(counts)

                from sklearn.linear_model import LinearRegression
                model = LinearRegression()
                model.fit(X, y)

                future_X = np.arange(len(counts), len(counts) + forecast_days).reshape(-1, 1)
                predictions = model.predict(future_X)

                forecast_dates = [(today + timedelta(days=i + 1)).strftime('%Y-%m-%d') for i in range(forecast_days)]
                forecast = [
                    {"date": forecast_dates[i], "predicted": int(max(0, predictions[i]))}
                    for i in range(forecast_days)
                ]

                return {
                    "forecast": forecast[:forecast_days],
                    "model": {
                        "type": "linear_regression",
                        "coefficient": round(float(model.coef_[0]), 4),
                        "intercept": round(float(model.intercept_), 2),
                        "r_squared": round(float(model.score(X, y)), 4)
                    },
                    "trend": "上升" if model.coef_[0] > 0.5 else ("下降" if model.coef_[0] < -0.5 else "平稳"),
                    "history_summary": {
                        "period": f"{dates[0]} 至 {dates[-1]}",
                        "total": int(np.sum(y)),
                        "avg_daily": round(float(np.mean(y)), 1)
                    }
                }

        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取预测失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取预测失败: {e}")


@router.post("/snapshot")
async def save_snapshot(snapshot: dict):
    cache_key = f"stats:snapshot:{snapshot.get('id', '')}"
    cache.cache_set(cache_key, snapshot, 3600 * 24)
    return {"status": "ok", "id": snapshot.get("id")}