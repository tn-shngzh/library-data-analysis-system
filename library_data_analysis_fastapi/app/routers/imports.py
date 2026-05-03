import logging
import csv
import io
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Query
from app.database import run_sync_db, get_db_connection, release_db_connection
from app.cache import cache
from app.auth import get_current_user
from app.tasks import mv_refresher

router = APIRouter(prefix="/api/imports", tags=["数据导入"])
logger = logging.getLogger(__name__)


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...), current_user=Depends(get_current_user)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="仅支持CSV文件")

    try:
        content = await file.read()
        text = content.decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(text))

        required = {'borrower_id', 'bib_id', 'action', 'action_date'}
        if not required.issubset(set(reader.fieldnames or [])):
            raise HTTPException(status_code=400, detail=f"CSV缺少必要列: {required}")

        rows = list(reader)
        imported = 0
        skipped = 0
        errors = []

        def _import(conn):
            nonlocal imported, skipped
            with conn.cursor() as cur:
                cur.execute("CREATE TABLE IF NOT EXISTS import_records (id SERIAL PRIMARY KEY, filename VARCHAR(255), imported_count INT DEFAULT 0, skipped_count INT DEFAULT 0, error_count INT DEFAULT 0, import_time TIMESTAMP DEFAULT NOW())")

                valid_actions = {'CKO', 'CKI', 'REH', 'REI'}
                valid_rows = []
                for i, row in enumerate(rows):
                    action = row.get('action', '').upper().strip()
                    if action not in valid_actions:
                        errors.append(f"第{i+2}行: 无效操作类型 '{action}'")
                        skipped += 1
                        continue
                    try:
                        action_date = int(row.get('action_date', '0'))
                    except ValueError:
                        errors.append(f"第{i+2}行: 无效日期格式")
                        skipped += 1
                        continue
                    valid_rows.append((row['borrower_id'].strip(), row['bib_id'].strip(), action, action_date))

                if valid_rows:
                    from psycopg2.extras import execute_values
                    execute_values(
                        cur,
                        "INSERT INTO circulations (borrower_id, bib_id, action, action_date) VALUES %s",
                        valid_rows
                    )
                    imported = len(valid_rows)

                cur.execute(
                    "INSERT INTO import_records (filename, imported_count, skipped_count, error_count) VALUES (%s, %s, %s, %s)",
                    (file.filename, imported, skipped, len(errors))
                )
            conn.commit()

        await run_sync_db(_import)
        cache.cache_clear()
        mv_refresher.schedule_refresh('mv_overview_stats', 'mv_borrow_stats', 'mv_book_stats', 'mv_reader_stats')

        return {
            "success": True,
            "imported": imported,
            "skipped": skipped,
            "errors": errors[:20]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("数据导入失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"数据导入失败: {e}")


@router.get("/history")
async def get_import_history(current_user=Depends(get_current_user)):
    cache_key = "imports:history"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        def _query(conn):
            with conn.cursor() as cur:
                cur.execute("CREATE TABLE IF NOT EXISTS import_records (id SERIAL PRIMARY KEY, filename VARCHAR(255), imported_count INT DEFAULT 0, skipped_count INT DEFAULT 0, error_count INT DEFAULT 0, import_time TIMESTAMP DEFAULT NOW())")
                cur.execute("SELECT id, filename, imported_count, skipped_count, error_count, import_time FROM import_records ORDER BY import_time DESC LIMIT 20")
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                return {"imports": [dict(zip(columns, row)) for row in rows]}

        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 30)
        return result
    except Exception as e:
        logger.error("获取导入历史失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取导入历史失败: {e}")


@router.post("/validate")
async def validate_csv(file: UploadFile = File(...), current_user=Depends(get_current_user)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="仅支持CSV文件")

    try:
        content = await file.read()
        text = content.decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(text))

        required = {'borrower_id', 'bib_id', 'action', 'action_date'}
        if not required.issubset(set(reader.fieldnames or [])):
            missing = required - set(reader.fieldnames or [])
            raise HTTPException(status_code=400, detail=f"CSV缺少必要列: {missing}")

        rows = list(reader)
        total_rows = len(rows)
        valid_rows = 0
        row_errors = []
        valid_actions = {'CKO', 'CKI', 'REH', 'REI'}

        for i, row in enumerate(rows):
            action = row.get('action', '').upper().strip()
            if action not in valid_actions:
                row_errors.append({"row": i + 2, "message": f"无效操作类型 '{action}'"})
                continue
            try:
                int(row.get('action_date', '0'))
            except ValueError:
                row_errors.append({"row": i + 2, "message": "无效日期格式"})
                continue
            if not row.get('borrower_id', '').strip():
                row_errors.append({"row": i + 2, "message": "借阅者ID为空"})
                continue
            if not row.get('bib_id', '').strip():
                row_errors.append({"row": i + 2, "message": "图书ID为空"})
                continue
            valid_rows += 1

        return {
            "valid": len(row_errors) == 0,
            "total_rows": total_rows,
            "valid_rows": valid_rows,
            "errors": row_errors[:50]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("数据验证失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"数据验证失败: {e}")
