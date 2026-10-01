"""Workers endpoint for the Soukchay API (data_entry + joined labor/loan/fa/follow-up).

This endpoint provides:
- Full worker records with all 31 Data Entry columns
- Joined data from labor_department, loan_department, fa_department, labor_follow_korea
- Stats by status
- Notification filtering (health, visa, departure, return)
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pymysql import Connection

from ..db import get_conn
from ..schemas import Worker, WorkerStats
from ..services.interest import (
    days_overdue,
    elapsed_term_days,
    interest_payable,
    over_under_amount,
    to_currency,
)
from ..auth import require_api_key


router = APIRouter(prefix="/workers", tags=["Workers"], dependencies=[Depends(require_api_key)])


def _get_worker(conn: Connection, cid: int) -> Optional[Dict]:
    """Fetch a single worker with all joined data (latest labor/follow-up row)."""
    q = """
    SELECT 
        de.*,
        ld.labor_type,
        lo.fin_price, lo.rate, lo.term, lo.first_due_date, lo.last_due_date, lo.ex_rate,
        fa.status AS fa_status,
        lf.fa_in_soun, lf.time_ex, lf.price_ex, lf.visa_form_date, lf.visa_to_date,
        lf.return_date, lf.run_date, lf.blacklist_date, lf.blacklist_remark,
        lf.return_korea, lf.re_korea, lf.early_date_fines, lf.early_remark, lf.date_kam,
        p.pro_name_lao AS province_lao, p.pro_name AS province,
        d.dis_name_lao AS district_lao, d.dis_name AS district,
        v.vill_name_lao AS village_lao, v.vill_name AS village,
        dk.disk_code,
        dk.disk_name_lao AS korea_district_lao,
        dk.disk_name AS korea_district_eng,
        pk.prok_name AS korea_province_lao,
        pk.prok_name AS korea_province_eng,
        de.emp_name AS employer_name
    FROM data_entry de
    LEFT JOIN (
        SELECT data_id, MAX(labor_id) AS labor_id
        FROM labor_department GROUP BY data_id
    ) ldmax ON ldmax.data_id = de.data_id
    LEFT JOIN labor_department ld ON ld.labor_id = ldmax.labor_id
    LEFT JOIN (
        SELECT cif, MAX(fol_id) AS fol_id
        FROM labor_follow_korea GROUP BY cif
    ) lfmax ON lfmax.cif = de.cif
    LEFT JOIN labor_follow_korea lf ON lf.fol_id = lfmax.fol_id
    LEFT JOIN loan_department lo ON de.cif = lo.cif
    LEFT JOIN fa_department fa ON de.cif = fa.cif
    LEFT JOIN district_korea dk ON LPAD(TRIM(de.emp_dis), 5, '0') = dk.disk_id
    LEFT JOIN province_korea pk ON dk.prok_id = pk.prok_id
    LEFT JOIN province p ON de.la_pro = p.pro_id
    LEFT JOIN district d ON de.la_dis = d.dis_id
    LEFT JOIN village v ON de.la_vill = v.vill_id
    WHERE de.data_id = %s
    ORDER BY de.id DESC
    LIMIT 1
    """
    with conn.cursor() as cur:
        cur.execute(q, (cid,))
        return cur.fetchone()


def _get_workers(
    conn: Connection, status: Optional[str] = None, notify: Optional[str] = None
) -> List[Dict]:
    """Fetch worker list with optional filters."""
    q = """
    SELECT 
        de.*,
        ld.labor_type,
        lo.fin_price, lo.rate, lo.term, lo.first_due_date, lo.last_due_date, lo.ex_rate,
        fa.status AS fa_status,
        lf.fa_in_soun, lf.time_ex, lf.price_ex, lf.visa_form_date, lf.visa_to_date,
        lf.return_date, lf.run_date, lf.blacklist_date, lf.blacklist_remark,
        lf.return_korea, lf.re_korea, lf.early_date_fines, lf.early_remark, lf.date_kam,
        p.pro_name_lao AS province_lao, p.pro_name AS province,
        d.dis_name_lao AS district_lao, d.dis_name AS district,
        v.vill_name_lao AS village_lao, v.vill_name AS village,
        dk.disk_code,
        dk.disk_name_lao AS korea_district_lao,
        dk.disk_name AS korea_district_eng,
        pk.prok_name AS korea_province_lao,
        pk.prok_name AS korea_province_eng,
        de.emp_name AS employer_name
    FROM data_entry de
    LEFT JOIN (
        SELECT data_id, MAX(labor_id) AS labor_id
        FROM labor_department GROUP BY data_id
    ) ldmax ON ldmax.data_id = de.data_id
    LEFT JOIN labor_department ld ON ld.labor_id = ldmax.labor_id
    LEFT JOIN (
        SELECT cif, MAX(fol_id) AS fol_id
        FROM labor_follow_korea GROUP BY cif
    ) lfmax ON lfmax.cif = de.cif
    LEFT JOIN labor_follow_korea lf ON lf.fol_id = lfmax.fol_id
    LEFT JOIN loan_department lo ON de.cif = lo.cif
    LEFT JOIN fa_department fa ON de.cif = fa.cif
    LEFT JOIN district_korea dk ON LPAD(TRIM(de.emp_dis), 5, '0') = dk.disk_id
    LEFT JOIN province_korea pk ON dk.prok_id = pk.prok_id
    LEFT JOIN province p ON de.la_pro = p.pro_id
    LEFT JOIN district d ON de.la_dis = d.dis_id
    LEFT JOIN village v ON de.la_vill = v.vill_id
    WHERE 1=1
    """
    params = []
    if status:
        q += " AND de.status = %s"
        params.append(status)
    if notify:
        today = "CURDATE()"
        if notify == "heal":
            q += " AND de.heal_date != '0000-00-00' AND de.heal_date BETWEEN %s AND DATE_ADD(%s, INTERVAL 7 DAY)"
            params.extend([today, today])
        elif notify == "visa":
            q += " AND (de.ccvi_is_date != '0000-00-00' AND de.ccvi_is_date BETWEEN %s AND DATE_ADD(%s, INTERVAL 7 DAY) OR de.ccvi_visa_date != '0000-00-00' AND de.ccvi_visa_date BETWEEN %s AND DATE_ADD(%s, INTERVAL 7 DAY))"
            params.extend([today, today, today, today])
        elif notify == "departure":
            q += " AND de.dep_date != '0000-00-00' AND de.dep_date BETWEEN %s AND DATE_ADD(%s, INTERVAL 7 DAY)"
            params.extend([today, today])
        elif notify == "return":
            q += " AND (lf.return_korea != '' OR lf.return_date != '0000-00-00')"
        elif notify == "enter_center":
            q += " AND lf.fa_in_soun != ''"
        else:
            q += " AND 1=0"  # Unknown notify type returns empty
    q += " ORDER BY de.data_id DESC"
    with conn.cursor() as cur:
        cur.execute(q, params)
        return cur.fetchall()


def _get_workers_stats(conn: Connection) -> Dict:
    """Get worker counts by status."""
    q = "SELECT status, COUNT(*) as count FROM data_entry GROUP BY status"
    with conn.cursor() as cur:
        cur.execute(q)
        stats = {row["status"]: row["count"] for row in cur.fetchall()}
        return {"total": sum(stats.values()), "by_status": stats}


@router.get("", response_model=List[Worker])
def list_workers(
    conn: Connection = Depends(get_conn),
    status: Optional[str] = Query(None, description="Filter by status"),
    notify: Optional[str] = Query(
        None, description="Filter by notification type (heal|visa|departure|return)"
    ),
):
    """List all workers with joined data."""
    return _get_workers(conn, status=status, notify=notify)


@router.get("/stats", response_model=WorkerStats)
def workers_stats(conn: Connection = Depends(get_conn)):
    """Get worker statistics by status."""
    return _get_workers_stats(conn)


@router.get("/{cid}", response_model=Worker)
def get_worker(cid: int, conn: Connection = Depends(get_conn)):
    """Get a single worker by CID with all joined data."""
    worker = _get_worker(conn, cid)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    return worker


@router.get("/{cid}/payments", response_model=List[Dict])
def get_worker_payments(cid: int, conn: Connection = Depends(get_conn)):
    """Get loan and visa payment history for a worker."""
    q = """
    SELECT
        play_id, play_cif, play_date, play_type, play_all, play_ment, play_balance,
        play_bank, play_currency, play_sc, play_accoun, user_add, user_add_date,
        user_edit, user_edit_date, play_rate, play_exchange, 'loan' AS source
    FROM playment
    WHERE play_cif IN (SELECT cif FROM data_entry WHERE data_id = %s AND cif <> '')
    UNION ALL
    SELECT
        play_id, play_cif, play_date, play_type, play_all, play_ment, play_balance,
        play_bank, play_currency, play_sc, play_accoun, user_add, user_add_date,
        user_edit, user_edit_date, play_rate, play_exchange, 'visa' AS source
    FROM playment2
    WHERE play_cif IN (SELECT cif FROM data_entry WHERE data_id = %s AND cif <> '')
    UNION ALL
    SELECT
        play_id, play_cif, play_date, play_type, play_all, play_ment, play_balance,
        play_bank, play_currency, play_sc, play_accoun, user_add, user_add_date,
        user_edit, user_edit_date, play_rate, play_exchange, 'visa2' AS source
    FROM playment3
    WHERE play_cif IN (SELECT cif FROM data_entry WHERE data_id = %s AND cif <> '')
    ORDER BY play_date DESC
    """
    with conn.cursor() as cur:
        cur.execute(q, (cid, cid, cid))
        return cur.fetchall()
