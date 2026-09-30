"""FA Department endpoint for the Soukchay API.

Provides FA department records with computed interest/days fields and payment history.
"""
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pymysql import Connection

from ...db import get_conn
from ...schemas import FaDepartment
from ...services.interest import days_overdue, elapsed_term_days, interest_payable, over_under_amount, to_currency


router = APIRouter(prefix="/fa-department", tags=["FA Department"])


def _get_fa_department(conn: Connection, fa_id: int) -> Optional[Dict]:
    """Fetch a single FA department record with computed fields."""
    q = """
    SELECT 
        fa.*,
        lo.fin_price, lo.rate, lo.term, lo.first_due_date, lo.last_due_date, lo.ex_rate,
        de.la_name, de.surname, de.la_lao_name, de.la_lao_sure,
        p.province_lao, p.province,
        d.district_lao, d.district,
        v.village_lao, v.village
    FROM fa_department fa
    JOIN loan_department lo ON fa.cif = lo.cif
    JOIN data_entry de ON fa.cif = de.cif
    LEFT JOIN province p ON de.la_pro = p.province_id
    LEFT JOIN district d ON de.la_dis = d.district_id
    LEFT JOIN village v ON de.la_vill = v.village_id
    WHERE fa.id = %s
    """
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(q, (fa_id,))
        record = cur.fetchone()
        if record:
            # Add computed fields
            record["days_overdue"] = days_overdue(record["first_due_date"], record["last_due_date"])
            record["elapsed_term_days"] = elapsed_term_days(record["first_due_date"])
            record["interest_payable"] = interest_payable(record["fin_price"], record["rate"], record["elapsed_term_days"])
            record["over_under_amount"] = over_under_amount(record["price4"], record["price4"])  # price4 is total debt
            # Currency conversions
            record["total_debt_lak"] = to_currency(record["price4"], record["ex_rate"])
            record["total_debt_usd"] = record["price4"]
        return record


def _get_fa_department_list(conn: Connection) -> List[Dict]:
    """Fetch all FA department records with computed fields."""
    q = """
    SELECT 
        fa.*,
        lo.fin_price, lo.rate, lo.term, lo.first_due_date, lo.last_due_date, lo.ex_rate,
        de.la_name, de.surname, de.la_lao_name, de.la_lao_sure,
        p.province_lao, p.province,
        d.district_lao, d.district,
        v.village_lao, v.village
    FROM fa_department fa
    JOIN loan_department lo ON fa.cif = lo.cif
    JOIN data_entry de ON fa.cif = de.cif
    LEFT JOIN province p ON de.la_pro = p.province_id
    LEFT JOIN district d ON de.la_dis = d.district_id
    LEFT JOIN village v ON de.la_vill = v.village_id
    ORDER BY fa.id DESC
    """
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(q)
        records = cur.fetchall()
        # Add computed fields to each record
        for record in records:
            record["days_overdue"] = days_overdue(record["first_due_date"], record["last_due_date"])
            record["elapsed_term_days"] = elapsed_term_days(record["first_due_date"])
            record["interest_payable"] = interest_payable(record["fin_price"], record["rate"], record["elapsed_term_days"])
            record["over_under_amount"] = over_under_amount(record["price4"], record["price4"])  # price4 is total debt
            # Currency conversions
            record["total_debt_lak"] = to_currency(record["price4"], record["ex_rate"])
            record["total_debt_usd"] = record["price4"]
        return records


def _get_fa_department_payments(conn: Connection, fa_id: int) -> List[Dict]:
    """Get payment history for an FA department record."""
    q = """
    SELECT 
        pl.*, pl.play_date, pl.play_all, pl.play_ment, pl.play_balance,
        pl.play_type, pl.play_bank, pl.play_currency, pl.play_sc, pl.play_accoun,
        pl2.play_date AS visa_date, pl2.play_all AS visa_amount,
        pl3.play_date AS visa_date2, pl3.play_all AS visa_amount2
    FROM fa_department fa
    LEFT JOIN playment pl ON fa.cif = pl.play_cif
    LEFT JOIN playment2 pl2 ON fa.cif = pl2.play_cif
    LEFT JOIN playment3 pl3 ON fa.cif = pl3.play_cif
    WHERE fa.id = %s
    ORDER BY pl.play_date DESC, pl2.play_date DESC, pl3.play_date DESC
    """
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(q, (fa_id,))
        return cur.fetchall()


@router.get("", response_model=List[FaDepartment])
def list_fa_department(conn: Connection = Depends(get_conn)):
    """List all FA department records."""
    return _get_fa_department_list(conn)


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