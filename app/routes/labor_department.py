"""Labor Department endpoint for the Soukchay API.

Provides labor department records with Korean placement details and statistics.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pymysql import Connection

from ..db import get_conn
from ..schemas import LaborDepartment, LaborDepartmentStats
from ..auth import require_api_key


router = APIRouter(prefix="/labor-department", tags=["Labor Department"], dependencies=[Depends(require_api_key)])


def _get_labor_department(conn: Connection, labor_id: int) -> Optional[Dict]:
    """Fetch a single labor department record with Korean details."""
    q = """
    SELECT 
        ld.*,
        de.ccvi_sub_date, de.ccvi_is_date, de.visa_sub_date, de.ccvi_visa_date,
        de.dep_date, de.due_date, de.bank_acc_no, de.bank_acc_no2,
        de.emp_name AS employer_name,
        dk.disk_code,
        dk.disk_name_lao AS korea_district_lao,
        dk.disk_name AS korea_district_eng,
        pk.prok_name AS korea_province_lao,
        pk.prok_name AS korea_province_eng
    FROM labor_department ld
    LEFT JOIN (
        SELECT data_id, MAX(id) AS id
        FROM data_entry GROUP BY data_id
    ) demax ON demax.data_id = ld.data_id
    LEFT JOIN data_entry de ON de.id = demax.id
    LEFT JOIN district_korea dk ON LPAD(TRIM(de.emp_dis), 5, '0') = dk.disk_id
    LEFT JOIN province_korea pk ON dk.prok_id = pk.prok_id
    WHERE ld.labor_id = %s
    """
    with conn.cursor() as cur:
        cur.execute(q, (labor_id,))
        return cur.fetchone()


def _get_labor_department_list(conn: Connection) -> List[Dict]:
    """Fetch all labor department records."""
    q = """
    SELECT 
        ld.*,
        de.ccvi_sub_date, de.ccvi_is_date, de.visa_sub_date, de.ccvi_visa_date,
        de.dep_date, de.due_date, de.bank_acc_no, de.bank_acc_no2,
        de.emp_name AS employer_name,
        dk.disk_code,
        dk.disk_name_lao AS korea_district_lao,
        dk.disk_name AS korea_district_eng,
        pk.prok_name AS korea_province_lao,
        pk.prok_name AS korea_province_eng
    FROM labor_department ld
    LEFT JOIN (
        SELECT data_id, MAX(id) AS id
        FROM data_entry GROUP BY data_id
    ) demax ON demax.data_id = ld.data_id
    LEFT JOIN data_entry de ON de.id = demax.id
    LEFT JOIN district_korea dk ON LPAD(TRIM(de.emp_dis), 5, '0') = dk.disk_id
    LEFT JOIN province_korea pk ON dk.prok_id = pk.prok_id
    ORDER BY ld.labor_id DESC
    """
    with conn.cursor() as cur:
        cur.execute(q)
        return cur.fetchall()


def _get_labor_department_stats(conn: Connection) -> Dict:
    """Get labor department statistics."""
    q = "SELECT labor_type, COUNT(*) as count FROM labor_department GROUP BY labor_type"
    with conn.cursor() as cur:
        cur.execute(q)
        stats = {row["labor_type"]: row["count"] for row in cur.fetchall()}
        return {"total": sum(stats.values()), "by_type": stats}


@router.get("", response_model=List[LaborDepartment])
def list_labor_department(conn: Connection = Depends(get_conn)):
    """List all labor department records."""
    return _get_labor_department_list(conn)


@router.get("/stats", response_model=LaborDepartmentStats)
def labor_department_stats(conn: Connection = Depends(get_conn)):
    """Get labor department statistics."""
    return _get_labor_department_stats(conn)


@router.get("/{labor_id}", response_model=LaborDepartment)
def get_labor_department(labor_id: int, conn: Connection = Depends(get_conn)):
    """Get a single labor department record."""
    record = _get_labor_department(conn, labor_id)
    if not record:
        raise HTTPException(status_code=404, detail="Labor department record not found")
    return record
