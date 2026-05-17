    def _query(conn):
        with conn.cursor() as cur:
            if start_date and end_date:
                cur.execute("""
                    SELECT TO_CHAR(TO_DATE(borrow_date::TEXT, 'YYYYMMDD'), 'YYYY-MM') as month,
                           COUNT(DISTINCT borrower_id) as active_count,
                           COUNT(*) as borrow_count
                    FROM circulations
                    WHERE borrow_date BETWEEN %s AND %s
                    GROUP BY month
                    ORDER BY month
                """, (start_date, end_date))
                rows = cur.fetchall()
                return [{"label": r[0], "value": r[1], "count": r[2]} for r in rows]
            else:
                cur.execute("""
                    SELECT TO_CHAR(TO_DATE(borrow_date::TEXT, 'YYYYMMDD'), 'YYYY-MM') as month,
                           COUNT(DISTINCT borrower_id) as active_count,
                           COUNT(*) as borrow_count
                    FROM circulations
                    GROUP BY month
                    ORDER BY month DESC
                    LIMIT 12
                """)
                rows = cur.fetchall()
                return [{"label": r[0], "value": r[1], "count": r[2]} for r in reversed(rows)]
