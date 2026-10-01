"""FA Department endpoint for the Soukchay API.

Provides FA department records with computed interest/days fields and payment history.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pymysql import Connection

from ..db import get_conn
from ..schemas import FaDepartment, FaDepartmentStats
from ..services.interest import (
    days_overdue,
    elapsed_term_days,
    interest_payable,
    over_under_amount,
    to_currency,
    to_lak,
)
from ..auth import require_api_key


router = APIRouter(prefix="/fa-department", tags=["FA Department"], dependencies=[Depends(require_api_key)])


def _get_payments_total(conn: Connection, cif: str) -> float:
    """Get total payments (loan + visa) for a CIF."""
    q = """
    SELECT COALESCE(SUM(CAST(play_ment AS DECIMAL(20,2))), 0) as total
    FROM (
        SELECT play_ment FROM playment WHERE play_cif = %s
        UNION ALL
        SELECT play_ment FROM playment2 WHERE play_cif = %s
        UNION ALL
        SELECT play_ment FROM playment3 WHERE play_cif = %s
    ) p
    """
    with conn.cursor() as cur:
        cur.execute(q, (cif, cif, cif))
        row = cur.fetchone()
        return float(row["total"] or 0.0) if row else 0.0


def _get_fa_department(conn: Connection, fa_id: int) -> Optional[Dict]:
    """Fetch a single FA department record with computed fields."""
    q = """
    SELECT 
        fa.*,
        lo.fin_price, lo.rate, lo.term, lo.first_due_date, lo.last_due_date, lo.ex_rate,
        lo.price4,
        de.la_eng_name, de.surname, de.la_lao_name, de.la_lao_sure,
        p.pro_name_lao AS province_lao, p.pro_name AS province,
        d.dis_name_lao AS district_lao, d.dis_name AS district,
        v.vill_name_lao AS village_lao, v.vill_name AS village
    FROM fa_department fa
    LEFT JOIN loan_department lo ON fa.cif = lo.cif
    LEFT JOIN (
        SELECT cif, MAX(id) AS id
        FROM data_entry GROUP BY cif
    ) demax ON demax.cif = fa.cif
    LEFT JOIN data_entry de ON de.id = demax.id
    LEFT JOIN province p ON de.la_pro = p.pro_id
    LEFT JOIN district d ON de.la_dis = d.dis_id
    LEFT JOIN village v ON de.la_vill = v.vill_id
    WHERE fa.fa_id = %s
    """
    with conn.cursor() as cur:
        cur.execute(q, (fa_id,))
        record = cur.fetchone()
        if record:
            # Add computed fields
            record["days_overdue"] = days_overdue(
                record["first_due_date"], record["last_due_date"]
            )
            record["elapsed_term_days"] = elapsed_term_days(record["first_due_date"])
            record["interest_payable"] = interest_payable(
                record["fin_price"], record["rate"], record["elapsed_term_days"]
            )
            # Calculate over/under amount from actual payments
            payments_total = _get_payments_total(conn, record["cif"])
            record["over_under_amount"] = over_under_amount(payments_total, record["price4"])
            # Currency conversions - price4 is already in LAK, ex_rate is LAK per USD
            if record.get("price4") is not None and record.get("ex_rate"):
                record["total_debt_usd"] = to_currency(record["price4"], record["ex_rate"])
                record["total_debt_lak"] = record["price4"]
            else:
                record["total_debt_lak"] = None
                record["total_debt_usd"] = None
        return record


def _get_fa_department_list(conn: Connection) -> List[Dict]:
    """Fetch all FA department records with computed fields."""
    q = """
    SELECT 
        fa.*,
        lo.fin_price, lo.rate, lo.term, lo.first_due_date, lo.last_due_date, lo.ex_rate,
        lo.price4,
        de.la_eng_name, de.surname, de.la_lao_name, de.la_lao_sure,
        p.pro_name_lao AS province_lao, p.pro_name AS province,
        d.dis_name_lao AS district_lao, d.dis_name AS district,
        v.vill_name_lao AS village_lao, v.vill_name AS village
    FROM fa_department fa
    LEFT JOIN loan_department lo ON fa.cif = lo.cif
    LEFT JOIN (
        SELECT cif, MAX(id) AS id
        FROM data_entry GROUP BY cif
    ) demax ON demax.cif = fa.cif
    LEFT JOIN data_entry de ON de.id = demax.id
    LEFT JOIN province p ON de.la_pro = p.pro_id
    LEFT JOIN district d ON de.la_dis = d.dis_id
    LEFT JOIN village v ON de.la_vill = v.vill_id
    ORDER BY fa.fa_id DESC
    """
    with conn.cursor() as cur:
        cur.execute(q)
        records = cur.fetchall()
        # Add computed fields to each record
        for record in records:
            record["days_overdue"] = days_overdue(
                record["first_due_date"], record["last_due_date"]
            )
            record["elapsed_term_days"] = elapsed_term_days(record["first_due_date"])
            record["interest_payable"] = interest_payable(
                record["fin_price"], record["rate"], record["elapsed_term_days"]
            )
            # Calculate over/under amount from actual payments
            payments_total = _get_payments_total(conn, record["cif"])
            record["over_under_amount"] = over_under_amount(payments_total, record["price4"])
            # Currency conversions - price4 is already in LAK, ex_rate is LAK per USD
            if record.get("price4") is not None and record.get("ex_rate"):
                record["total_debt_usd"] = to_currency(record["price4"], record["ex_rate"])
                record["total_debt_lak"] = record["price4"]
            else:
                record["total_debt_lak"] = None
                record["total_debt_usd"] = None
        return records


def _get_fa_department_stats(conn: Connection) -> Dict:
    """Get FA department statistics."""
    q = "SELECT status, COUNT(*) as count FROM fa_department GROUP BY status"
    with conn.cursor() as cur:
        cur.execute(q)
        stats = {row["status"]: row["count"] for row in cur.fetchall()}
        return {
            "total": sum(stats.values()),
            "by_status": stats
        }


def _get_fa_department_payments(conn: Connection, fa_id: int) -> List[Dict]:
    """Get payment history for an FA department record."""
    q = """
    SELECT
        play_id, play_cif, play_date, play_type, play_all, play_ment, play_balance,
        play_bank, play_currency, play_sc, play_accoun, user_add, user_add_date,
        user_edit, user_edit_date, play_rate, play_exchange, 'loan' AS source
    FROM playment
    WHERE play_cif = (SELECT cif FROM fa_department WHERE fa_id = %s)
    UNION ALL
    SELECT
        play_id, play_cif, play_date, play_type, play_all, play_ment, play_balance,
        play_bank, play_currency, play_sc, play_accoun, user_add, user_add_date,
        user_edit, user_edit_date, play_rate, play_exchange, 'visa' AS source
    FROM playment2
    WHERE play_cif = (SELECT cif FROM fa_department WHERE fa_id = %s)
    UNION ALL
    SELECT
        play_id, play_cif, play_date, play_type, play_all, play_ment, play_balance,
        play_bank, play_currency, play_sc, play_accoun, user_add, user_add_date,
        user_edit, user_edit_date, play_rate, play_exchange, 'visa2' AS source
    FROM playment3
    WHERE play_cif = (SELECT cif FROM fa_department WHERE fa_id = %s)
    ORDER BY play_date DESC
    """
    with conn.cursor() as cur:
        cur.execute(q, (fa_id, fa_id, fa_id))
        return cur.fetchall()


@router.get("", response_model=List[FaDepartment])
def list_fa_department(conn: Connection = Depends(get_conn)):
    """List all FA department records."""
    return _get_fa_department_list(conn)


@router.get("/stats", response_model=FaDepartmentStats)
def fa_department_stats(conn: Connection = Depends(get_conn)):
    """Get FA department statistics."""
    return _get_fa_department_stats(conn)


@router.get("/{fa_id}", response_model=FaDepartment)
def get_fa_department(fa_id: int, conn: Connection = Depends(get_conn)):
    """Get a single FA department record."""
    record = _get_fa_department(conn, fa_id)
    if not record:
        raise HTTPException(status_code=404, detail="FA department record not found")
    return record


@router.get("/{fa_id}/payments", response_model=List[Dict])
def get_fa_department_payments(fa_id: int, conn: Connection = Depends(get_conn)):
    """Get payment history for an FA department record."""
    return _get_fa_department_payments(conn, fa_id)
