"""Loan Department endpoint for the Soukchay API.

Provides loan department records with computed interest/days fields.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pymysql import Connection

from ..db import get_conn
from ..schemas import LoanDepartment, LoanDepartmentStats
from ..services.interest import (
    days_overdue,
    elapsed_term_days,
    interest_payable,
    over_under_amount,
)
from ..auth import require_api_key


router = APIRouter(prefix="/loan-department", tags=["Loan Department"], dependencies=[Depends(require_api_key)])


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


def _get_loan_department(conn: Connection, loan_id: int) -> Optional[Dict]:
    """Fetch a single loan department record with computed fields."""
    q = """
    SELECT 
        lo.*,
        de.la_eng_name, de.surname, de.la_lao_name, de.la_lao_sure,
        p.pro_name_lao AS province_lao, p.pro_name AS province,
        d.dis_name_lao AS district_lao, d.dis_name AS district,
        v.vill_name_lao AS village_lao, v.vill_name AS village
    FROM loan_department lo
    LEFT JOIN (
        SELECT cif, MAX(id) AS id
        FROM data_entry GROUP BY cif
    ) demax ON demax.cif = lo.cif
    LEFT JOIN data_entry de ON de.id = demax.id
    LEFT JOIN province p ON de.la_pro = p.pro_id
    LEFT JOIN district d ON de.la_dis = d.dis_id
    LEFT JOIN village v ON de.la_vill = v.vill_id
    WHERE lo.loan_id = %s
    """
    with conn.cursor() as cur:
        cur.execute(q, (loan_id,))
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
        return record


def _get_loan_department_list(conn: Connection) -> List[Dict]:
    """Fetch all loan department records with computed fields."""
    q = """
    SELECT 
        lo.*,
        de.la_eng_name, de.surname, de.la_lao_name, de.la_lao_sure,
        p.pro_name_lao AS province_lao, p.pro_name AS province,
        d.dis_name_lao AS district_lao, d.dis_name AS district,
        v.vill_name_lao AS village_lao, v.vill_name AS village
    FROM loan_department lo
    LEFT JOIN (
        SELECT cif, MAX(id) AS id
        FROM data_entry GROUP BY cif
    ) demax ON demax.cif = lo.cif
    LEFT JOIN data_entry de ON de.id = demax.id
    LEFT JOIN province p ON de.la_pro = p.pro_id
    LEFT JOIN district d ON de.la_dis = d.dis_id
    LEFT JOIN village v ON de.la_vill = v.vill_id
    ORDER BY lo.loan_id DESC
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
        return records


def _get_loan_department_stats(conn: Connection) -> Dict:
    """Get loan department statistics."""
    q = "SELECT sts_insert as status, COUNT(*) as count FROM loan_department GROUP BY sts_insert"
    with conn.cursor() as cur:
        cur.execute(q)
        stats = {row["status"]: row["count"] for row in cur.fetchall()}
        return {
            "total": sum(stats.values()),
            "by_status": stats
        }


@router.get("", response_model=List[LoanDepartment])
def list_loan_department(conn: Connection = Depends(get_conn)):
    """List all loan department records."""
    return _get_loan_department_list(conn)


@router.get("/stats", response_model=LoanDepartmentStats)
def loan_department_stats(conn: Connection = Depends(get_conn)):
    """Get loan department statistics."""
    return _get_loan_department_stats(conn)


@router.get("/{loan_id}", response_model=LoanDepartment)
def get_loan_department(loan_id: int, conn: Connection = Depends(get_conn)):
    """Get a single loan department record."""
    record = _get_loan_department(conn, loan_id)
    if not record:
        raise HTTPException(status_code=404, detail="Loan department record not found")
    return record
