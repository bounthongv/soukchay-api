"""Loan Department endpoint for the Soukchay API.

Provides loan department records with computed interest/days fields.
"""
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pymysql import Connection

from ...db import get_conn
from ...schemas import LoanDepartment
from ...services.interest import days_overdue, elapsed_term_days, interest_payable, over_under_amount


router = APIRouter(prefix="/loan-department", tags=["Loan Department"])


def _get_loan_department(conn: Connection, loan_id: int) -> Optional[Dict]:
    """Fetch a single loan department record with computed fields."""
    q = """
    SELECT 
        lo.*,
        de.la_name, de.surname, de.la_lao_name, de.la_lao_sure,
        p.province_lao, p.province,
        d.district_lao, d.district,
        v.village_lao, v.village
    FROM loan_department lo
    JOIN data_entry de ON lo.cif = de.cif
    LEFT JOIN province p ON de.la_pro = p.province_id
    LEFT JOIN district d ON de.la_dis = d.district_id
    LEFT JOIN village v ON de.la_vill = v.village_id
    WHERE lo.id = %s
    """
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(q, (loan_id,))
        record = cur.fetchone()
        if record:
            # Add computed fields
            record["days_overdue"] = days_overdue(record["first_due_date"], record["last_due_date"])
            record["elapsed_term_days"] = elapsed_term_days(record["first_due_date"])
            record["interest_payable"] = interest_payable(record["fin_price"], record["rate"], record["elapsed_term_days"])
            record["over_under_amount"] = over_under_amount(record["price4"], record["price4"])  # price4 is total debt
        return record


def _get_loan_department_list(conn: Connection) -> List[Dict]:
    """Fetch all loan department records with computed fields."""
    q = """
    SELECT 
        lo.*,
        de.la_name, de.surname, de.la_lao_name, de.la_lao_sure,
        p.province_lao, p.province,
        d.district_lao, d.district,
        v.village_lao, v.village
    FROM loan_department lo
    JOIN data_entry de ON lo.cif = de.cif
    LEFT JOIN province p ON de.la_pro = p.province_id
    LEFT JOIN district d ON de.la_dis = d.district_id
    LEFT JOIN village v ON de.la_vill = v.village_id
    ORDER BY lo.id DESC
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
        return records


@router.get("", response_model=List[LoanDepartment])
def list_loan_department(conn: Connection = Depends(get_conn)):
    """List all loan department records."""
    return _get_loan_department_list(conn)


@router.get("/{loan_id}", response_model=LoanDepartment)
def get_loan_department(loan_id: int, conn: Connection = Depends(get_conn)):
    """Get a single loan department record."""
    record = _get_loan_department(conn, loan_id)
    if not record:
        raise HTTPException(status_code=404, detail="Loan department record not found")
    return record