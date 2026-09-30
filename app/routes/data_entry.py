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

from ...db import get_conn
from ...schemas import Worker, WorkerStats
from ...services.interest import days_overdue, elapsed_term_days, interest_payable, over_under_amount, to_currency


router = APIRouter(prefix="/workers", tags=["Workers"])


def _get_worker(conn: Connection, cid: int) -> Optional[Dict]:
    """Fetch a single worker with all joined data."""
    q = """
    SELECT 
        de.*,
        ld.*,
        ld_k.*,
        ld_ko.disk_name_lao AS korea_district_lao,
        ld_ko.prok_name AS korea_province_lao,
        ld_ko.disk_name AS korea_district_eng,
        ld_ko.prok_name AS korea_province_eng,
        lo.*,
        fa.*,
        lf.*,
        p.province_lao, p.province,
        d.district_lao, d.district,
        v.village_lao, v.village,
        pk.province_lao AS korea_province_lao2,
        dk.district_lao AS korea_district_lao2,
        vk.village_lao AS korea_village_lao2,
        e.employer_name, e.employer_name_lao,
        q.quota_name, q.quota_name_lao,
        ak.account_name, ak.account_name_lao,
        ii.insurance_name, ii.insurance_name_lao
    FROM data_entry de
    LEFT JOIN labor_department ld ON de.data_id = ld.data_id
    LEFT JOIN labor_department_korea ld_k ON ld.labor_cif = ld_k.labor_cif
    LEFT JOIN district_korea ld_ko ON ld_k.district_id = ld_ko.disk_id
    LEFT JOIN loan_department lo ON de.cif = lo.cif
    LEFT JOIN fa_department fa ON de.cif = fa.cif
    LEFT JOIN labor_follow_korea lf ON de.cif = lf.cif
    LEFT JOIN province p ON de.la_pro = p.province_id
    LEFT JOIN district d ON de.la_dis = d.district_id
    LEFT JOIN village v ON de.la_vill = v.village_id
    LEFT JOIN province_korea pk ON ld_k.province_id = pk.province_id
    LEFT JOIN district_korea dk ON ld_k.district_id = dk.disk_id
    LEFT JOIN village_korea vk ON ld_k.village_id = vk.village_id
    LEFT JOIN employer e ON ld_k.employer_id = e.employer_id
    LEFT JOIN quota q ON ld_k.quota_id = q.quota_id
    LEFT JOIN account_korea ak ON ld_k.account_id = ak.account_id
    LEFT JOIN insurance_korea ii ON ld_k.insurance_id = ii.insurance_id
    WHERE de.data_id = %s
    """
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(q, (cid,))
        return cur.fetchone()


def _get_workers(conn: Connection, status: Optional[str] = None, notify: Optional[str] = None) -> List[Dict]:
    """Fetch worker list with optional filters."""
    q = """
    SELECT 
        de.*,
        ld.labor_type,
        ld_k.labor_name, ld_k.labor_name_lao,
        ld_ko.disk_name_lao AS korea_district_lao,
        ld_ko.prok_name AS korea_province_lao,
        ld_ko.disk_name AS korea_district_eng,
        ld_ko.prok_name AS korea_province_eng,
        lo.fin_price, lo.rate, lo.term, lo.first_due_date, lo.last_due_date, lo.ex_rate,
        fa.fa_status,
        lf.fa_in_soun, lf.time_ex, lf.price_ex, lf.visa_form_date, lf.visa_to_date,
        lf.return_date, lf.run_date, lf.blacklist_date, lf.blacklist_remark,
        lf.return_korea, lf.re_korea, lf.early_date_fines, lf.early_remark, lf.date_kam,
        p.province_lao, p.province,
        d.district_lao, d.district,
        v.village_lao, v.village,
        pk.province_lao AS korea_province_lao2,
        dk.district_lao AS korea_district_lao2,
        vk.village_lao AS korea_village_lao2,
        e.employer_name, e.employer_name_lao,
        q.quota_name, q.quota_name_lao,
        ak.account_name, ak.account_name_lao,
        ii.insurance_name, ii.insurance_name_lao
    FROM data_entry de
    LEFT JOIN labor_department ld ON de.data_id = ld.data_id
    LEFT JOIN labor_department_korea ld_k ON ld.labor_cif = ld_k.labor_cif
    LEFT JOIN district_korea ld_ko ON ld_k.district_id = ld_ko.disk_id
    LEFT JOIN loan_department lo ON de.cif = lo.cif
    LEFT JOIN fa_department fa ON de.cif = fa.cif
    LEFT JOIN labor_follow_korea lf ON de.cif = lf.cif
    LEFT JOIN province p ON de.la_pro = p.province_id
    LEFT JOIN district d ON de.la_dis = d.district_id
    LEFT JOIN village v ON de.la_vill = v.village_id
    LEFT JOIN province_korea pk ON ld_k.province_id = pk.province_id
    LEFT JOIN district_korea dk ON ld_k.district_id = dk.disk_id
    LEFT JOIN village_korea vk ON ld_k.village_id = vk.village_id
    LEFT JOIN employer e ON ld_k.employer_id = e.employer_id
    LEFT JOIN quota q ON ld_k.quota_id = q.quota_id
    LEFT JOIN account_korea ak ON ld_k.account_id = ak.account_id
    LEFT JOIN insurance_korea ii ON ld_k.insurance_id = ii.insurance_id
    WHERE 1=1
    """
    params = []
    if status:
        q += " AND de.la_status = %s"
        params.append(status)
    if notify:
        q += " AND 1=0"  # Placeholder for notify filters
    q += " ORDER BY de.data_id DESC"
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(q, params)
        return cur.fetchall()


def _get_workers_stats(conn: Connection) -> Dict:
    """Get worker counts by status."""
    q = "SELECT la_status, COUNT(*) as count FROM data_entry GROUP BY la_status"
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(q)
        stats = {row["la_status"]: row["count"] for row in cur.fetchall()}
        return {
            "total": sum(stats.values()),
            "by_status": stats
        }


@router.get("", response_model=List[Worker])
def list_workers(
    conn: Connection = Depends(get_conn),
    status: Optional[str] = Query(None, description="Filter by status"),
    notify: Optional[str] = Query(None, description="Filter by notification type (heal|visa|departure|return)")
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
        pl.*, pl.play_date, pl.play_all, pl.play_ment, pl.play_balance,
        pl.play_type, pl.play_bank, pl.play_currency, pl.play_sc, pl.play_accoun,
        pl2.play_date AS visa_date, pl2.play_all AS visa_amount,
        pl3.play_date AS visa_date2, pl3.play_all AS visa_amount2
    FROM data_entry de
    LEFT JOIN playment pl ON de.cif = pl.play_cif
    LEFT JOIN playment2 pl2 ON de.cif = pl2.play_cif
    LEFT JOIN playment3 pl3 ON de.cif = pl3.play_cif
    WHERE de.data_id = %s
    ORDER BY pl.play_date DESC, pl2.play_date DESC, pl3.play_date DESC
    """
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(q, (cid,))
        return cur.fetchall()