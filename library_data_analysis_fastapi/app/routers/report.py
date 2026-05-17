"""
报告生成路由
支持四类报告（综合/读者/图书/借阅）
流式输出 + AI 审查 + Excel/Word 导出
"""
import json
import logging
from datetime import datetime
from typing import AsyncIterator
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.auth import get_current_user
from app.database import run_sync_db
from app.services.llm import (
    check_llm_status, call_llm_sync, review_with_llm
)
from app.services.export import (
    make_excel_for_overview, make_excel_for_reader,
    make_excel_for_book, make_excel_for_borrow, make_docx
)

router = APIRouter(prefix="/api/reports", tags=["AI 报告"])
logger = logging.getLogger(__name__)


async def get_overview_data() -> dict:
    """获取综合概览数据"""
    
    def _query(conn):
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'returned') as total_returns,
                    COUNT(DISTINCT borrower_id) as active_readers,
                    COUNT(DISTINCT bib_id) as total_books
                FROM circulations
                WHERE status = 'borrowed'
            """)
            row = cur.fetchone()
            total_circ = row[0] or 0
            total_returns = row[1] or 0
            active_readers = row[2] or 0
            total_books = row[3] or 0

            cur.execute("SELECT COUNT(*) FROM borrowers")
            total_readers = cur.fetchone()[0] or 0

            cur.execute("SELECT COUNT(DISTINCT category) FROM book_categories")
            categories = cur.fetchone()[0] or 0

            cur.execute("SELECT MAX(borrow_date) FROM circulations WHERE status = 'borrowed'")
            max_date_row = cur.fetchone()
            max_date = max_date_row[0] if max_date_row and max_date_row[0] else 0
            if max_date > 0:
                cutoff = max_date - 100
            else:
                cutoff = 0

            cur.execute("""
                SELECT (borrow_date / 100) as ym,
                    SUM(CASE WHEN status = 'borrowed' THEN 1 ELSE 0 END) as cko,
                    SUM(CASE WHEN status = 'returned' THEN 1 ELSE 0 END) as cki,
                    COUNT(DISTINCT borrower_id) as active
                FROM circulations
                WHERE borrow_date >= %s
                GROUP BY ym
                ORDER BY ym DESC
                LIMIT 12
            """, (cutoff,))
            monthly = [
                {"month": str(r[0]), "借出": r[1] or 0, "归还": r[2] or 0,
                 "续借": 0, "网上续借": 0, "活跃读者": r[3] or 0}
                for r in cur.fetchall()
            ]

            return {
                "total_borrows": total_circ,
                "total_returns": total_returns,
                "total_renewals": total_circ + total_returns,
                "active_readers": active_readers,
                "total_books": total_books,
                "total_readers": total_readers,
                "categories": categories,
                "monthly": monthly,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    return await run_sync_db(_query)


async def get_reader_data() -> dict:
    """获取读者报告数据"""
    from app.config import education_levels
    
    def _query(conn):
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM borrowers")
            total_readers = cur.fetchone()[0] or 0

            cur.execute("SELECT COUNT(*) FROM borrowers WHERE id IN (SELECT DISTINCT borrower_id FROM circulations WHERE status = 'borrowed')")
            active_readers = cur.fetchone()[0] or 0
            
            cur.execute("""
                SELECT b.degree, COUNT(*) as cnt
                FROM borrowers b
                GROUP BY b.degree
                ORDER BY cnt DESC
            """)
            degree_dist = [
                {"学历": education_levels.get(r[0], r[0]), "人数": r[1]}
                for r in cur.fetchall()
            ]
            
            cur.execute("""
                SELECT b.degree, COUNT(*) as cnt
                FROM circulations c
                JOIN borrowers b ON c.borrower_id = b.id
                WHERE c.status = 'borrowed'
                GROUP BY b.degree
                ORDER BY cnt DESC
                LIMIT 10
            """)
            top_readers = [
                {"排名": i+1, "学历": education_levels.get(r[0], r[0]), "借阅次数": r[1]}
                for i, r in enumerate(cur.fetchall())
            ]
            
            return {
                "总读者数": total_readers,
                "活跃读者": active_readers,
                "活跃率": f"{(active_readers/total_readers*100):.1f}%" if total_readers else "0%",
                "学历分布": degree_dist,
                "TOP活跃读者": top_readers,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    return await run_sync_db(_query)


async def get_book_data() -> dict:
    """获取图书报告数据"""
    
    def _query(conn):
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM book_categories")
            total_books = cur.fetchone()[0] or 0
            
            cur.execute("""
                SELECT bc.category, COUNT(DISTINCT bc.bib_id) as book_cnt,
                       COUNT(c.id) as borrow_cnt
                FROM book_categories bc
                LEFT JOIN circulations c ON bc.bib_id = c.bib_id AND c.status = 'borrowed'
                GROUP BY bc.category
                ORDER BY borrow_cnt DESC
            """)
            categories = [
                {"分类": r[0] or "未知", "图书数": r[1], "借阅次数": r[2]}
                for r in cur.fetchall()
            ]
            
            cur.execute("""
                SELECT bc.name, bc.category, COUNT(c.id) as borrow_cnt
                FROM book_categories bc
                LEFT JOIN circulations c ON bc.bib_id = c.bib_id AND c.status = 'borrowed'
                GROUP BY bc.bib_id, bc.name, bc.category
                ORDER BY borrow_cnt DESC
                LIMIT 10
            """)
            hot_books = [
                {"书名": r[0] or r[1] or "未知", "分类": r[1] or "未知", "借阅次数": r[2]}
                for r in cur.fetchall()
            ]
            
            return {
                "总分类数": len(set(c["分类"] for c in categories)),
                "总图书数": total_books,
                "分类统计": categories[:10],
                "热门图书": hot_books,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    return await run_sync_db(_query)


async def get_borrow_data() -> dict:
    """获取借阅报告数据"""
    
    def _query(conn):
        with conn.cursor() as cur:
            cur.execute("""
                SELECT status, COUNT(*) as cnt
                FROM circulations
                WHERE status IN ('borrowed', 'returned')
                GROUP BY status
            """)
            action_dist = {r[0]: r[1] for r in cur.fetchall()}
            
            total = sum(action_dist.values())
            cko = action_dist.get("borrowed", 0)
            cki = action_dist.get("returned", 0)
            reh = 0
            rei = 0
            
            cur.execute("""
                SELECT (borrow_date / 100) as ym,
                    SUM(CASE WHEN status = 'borrowed' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN status = 'returned' THEN 1 ELSE 0 END)
                FROM circulations
                WHERE borrow_date > 0
                GROUP BY ym
                ORDER BY ym DESC
                LIMIT 12
            """)
            monthly = [
                {"月份": str(r[0]), "借出": r[1] or 0, "归还": r[2] or 0,
                 "续借": 0, "网上续借": 0}
                for r in cur.fetchall()
            ]
            
            return {
                "总借阅量": total,
                "借出": cko,
                "归还": cki,
                "馆内续借": reh,
                "网上续借": rei,
                "借出率": f"{(cko/total*100):.1f}%" if total else "0%",
                "月度趋势": monthly,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    return await run_sync_db(_query)


def build_report_prompt(data: dict, report_type: str) -> tuple[str, str]:
    """构建报告提示词"""
    data_str = json.dumps(data, ensure_ascii=False, indent=2)
    
    prompts = {
        "overview": {
            "user": f"""# Role
你是资深图书馆数据分析师。

# Data
{data_str}

# Task
基于以上综合数据，生成一份中文数据分析报告：
1. 数据概览：描述总借阅量、活跃读者、馆藏等核心指标
2. 深度分析：解释数据趋势和原因
3. 建议措施：提出改进建议

# Style
简洁清晰、通俗易懂、结论先行。

# Output
Markdown 格式，约200字。"""
        },
        "reader": {
            "user": f"""# Role
你是资深图书馆数据分析师。

# Data
{data_str}

# Task
基于以上读者数据，生成一份中文读者分析报告：
1. 数据概览：描述总读者、活跃率等核心指标
2. 深度分析：分析读者结构和活跃度
3. 建议措施：提出提升读者活跃度的建议

# Style
简洁清晰、通俗易懂。

# Output
Markdown 格式，约200字。"""
        },
        "book": {
            "user": f"""# Role
你是资深图书馆数据分析师。

# Data
{data_str}

# Task
基于以上图书数据，生成一份中文图书分析报告：
1. 数据概览：描述馆藏量、分类分布等核心指标
2. 深度分析：分析热门分类和冷门分类
3. 建议措施：提出优化馆藏的建议

# Style
简洁清晰、通俗易懂。

# Output
Markdown 格式，约200字。"""
        },
        "borrow": {
            "user": f"""# Role
你是资深图书馆数据分析师。

# Data
{data_str}

# Task
基于以上借阅数据，生成一份中文借阅分析报告：
1. 数据概览：描述借出、归还、续借等核心指标
2. 深度分析：分析借阅趋势和操作类型分布
3. 建议措施：提出优化借阅服务的建议

# Style
简洁清晰、通俗易懂。

# Output
Markdown 格式，约200字。"""
        }
    }
    
    system = "你是一个专业的数据分析师，用简洁清晰的中文输出报告。"
    return system, prompts.get(report_type, prompts["overview"])["user"]


def build_review_prompt(content: str, data: dict) -> tuple[str, str]:
    """构建审查提示词"""
    system = "你是一个严格的报告审核员，检查报告是否与数据一致，只输出修正后的内容或 REVIEW_PASS。"
    user = f"""# Role
你是资深报告质量审核员。

请审核以下报告是否：
1. 数据准确性：报告中的数字与数据一致，无幻觉
2. 逻辑连贯性：分析推理是否成立
3. 格式规范性：结构清晰、表达通顺

原始数据：
{json.dumps(data, ensure_ascii=False, indent=2)}

待审核报告：
{content}

如果有问题，直接输出修正后的完整报告。如果没问题，输出"REVIEW_PASS"。"""
    return system, user


@router.get("/status")
async def check_status(current_user=Depends(get_current_user)):
    """检查 LLM 服务状态"""
    return check_llm_status()


@router.get("/overview")
async def generate_overview_report(current_user=Depends(get_current_user)):
    """生成综合概览报告"""
    try:
        data = await get_overview_data()
        system, prompt = build_report_prompt(data, "overview")
        
        content = call_llm_sync(prompt, system)
        
        reviewed = review_with_llm(content, data, "")
        if reviewed == content:
            pass
        else:
            content = reviewed
        
        return {
            "content": content,
            "data": data,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error("综合报告生成失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"综合报告生成失败: {e}")


@router.get("/reader")
async def generate_reader_report(current_user=Depends(get_current_user)):
    """生成读者报告"""
    try:
        data = await get_reader_data()
        system, prompt = build_report_prompt(data, "reader")
        
        content = call_llm_sync(prompt, system)
        reviewed = review_with_llm(content, data, "")
        if reviewed != content:
            content = reviewed
        
        return {
            "content": content,
            "data": data,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error("读者报告生成失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"读者报告生成失败: {e}")


@router.get("/book")
async def generate_book_report(current_user=Depends(get_current_user)):
    """生成图书报告"""
    try:
        data = await get_book_data()
        system, prompt = build_report_prompt(data, "book")
        
        content = call_llm_sync(prompt, system)
        reviewed = review_with_llm(content, data, "")
        if reviewed != content:
            content = reviewed
        
        return {
            "content": content,
            "data": data,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error("图书报告生成失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"图书报告生成失败: {e}")


@router.get("/borrow")
async def generate_borrow_report(current_user=Depends(get_current_user)):
    """生成借阅报告"""
    try:
        data = await get_borrow_data()
        system, prompt = build_report_prompt(data, "borrow")
        
        content = call_llm_sync(prompt, system)
        reviewed = review_with_llm(content, data, "")
        if reviewed != content:
            content = reviewed
        
        return {
            "content": content,
            "data": data,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error("借阅报告生成失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"借阅报告生成失败: {e}")


@router.get("/export/excel/{report_type}")
async def export_excel(
    report_type: str,
    current_user=Depends(get_current_user)
):
    """导出 Excel 数据表"""
    import io
    try:
        data_funcs = {
            "overview": get_overview_data,
            "reader": get_reader_data,
            "book": get_book_data,
            "borrow": get_borrow_data
        }
        
        if report_type not in data_funcs:
            raise HTTPException(status_code=400, detail="不支持的报告类型")
        
        data = await data_funcs[report_type]()
        excel_bytes = {
            "overview": make_excel_for_overview,
            "reader": make_excel_for_reader,
            "book": make_excel_for_book,
            "borrow": make_excel_for_borrow
        }[report_type](data)
        
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"数据报告_{report_type}_{ts}.xlsx"
        
        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Excel导出失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Excel导出失败: {e}")


@router.get("/export/word")
async def export_word(
    report_type: str,
    content: str,
    current_user=Depends(get_current_user)
):
    """导出 Word 报告"""
    import io
    try:
        title_map = {
            "overview": "综合概览数据分析报告",
            "reader": "读者分析报告",
            "book": "图书分析报告",
            "borrow": "借阅分析报告"
        }
        
        title = title_map.get(report_type, "数据分析报告")
        docx_bytes = make_docx(title, content)
        
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{title}_{ts}.docx"
        
        return StreamingResponse(
            io.BytesIO(docx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error("Word导出失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Word导出失败: {e}")
