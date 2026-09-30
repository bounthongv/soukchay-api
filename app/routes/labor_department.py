"""Labor Department endpoint for the Soukchay API.

Provides labor department records with Korean placement details and statistics.
"""
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pymysql import Connection

from ...db import get_conn
from ...schemas import LaborDepartment, LaborDepartmentStats


router = APIRouter(prefix="/labor-department", tags=["Labor Department"])


def _get_labor_department(conn: Connection, labor_id: int) -> Optional[Dict]:
    """Fetch a single labor department record with Korean details."""
    q = """
    SELECT 
        ld.*,
        ld_k.*,
        ld_ko.disk_name_lao AS korea_district_lao,
        ld_ko.prok_name AS korea_province_lao,
        ld_ko.disk_name AS korea_district_eng,
        ld_ko.prok_name AS korea_province_eng,
        pk.province_lao AS korea_province_lao2,
        dk.district_lao AS korea_district_lao2,
        vk.village_lao AS korea_village_lao2,
        e.employer_name, e.employer_name_lao,
        q.quota_name, q.quota_name_lao,
        ak.account_name, ak.account_name_lao,
        ii.insurance_name, ii.insurance_name_lao
    FROM labor_department ld
    LEFT JOIN labor_department_korea ld_k ON ld.labor_cif = ld_k.labor_cif
    LEFT JOIN district_korea ld_ko ON ld_k.district_id = ld_ko.disk_id
    LEFT JOIN province_korea pk ON ld_k.province_id = pk.province_id
    LEFT JOIN district_korea dk ON ld_k.district_id = dk.disk_id
    LEFT JOIN village_korea vk ON ld_k.village_id = vk.village_id
    LEFT JOIN employer e ON ld_k.employer_id = e.employer_id
    LEFT JOIN quota q ON ld_k.quota_id = q.quota_id
    LEFT JOIN account_korea ak ON ld_k.account_id = ak.account_id
    LEFT JOIN insurance_korea ii ON ld_k.insurance_id = ii.insurance_id
    WHERE ld.id = %s
    """
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(q, (labor_id,))
        return cur.fetchone()


def _get_labor_department_list(conn: Connection) -> List[Dict]:
    """Fetch all labor department records."""
    q = """
    SELECT 
        ld.*,
        ld_k.*,
        ld_ko.disk_name_lao AS korea_district_lao,
        ld_ko.prok_name AS korea_province_lao,
        ld_ko.disk_name AS korea_district_eng,
        ld_ko.prok_name AS korea_province_eng,
        pk.province_lao AS korea_province_lao2,
        dk.district_lao AS korea_district_lao2,
        vk.village_lao AS korea_village_lao2,
        e.employer_name, e.employer_name_lao,
        q.quota_name, q.quota_name_lao,
        ak.account_name, ak.account_name_lao,
        ii.insurance_name, ii.insurance_name_lao
    FROM labor_department ld
    LEFT JOIN labor_department_korea ld_k ON ld.labor_cif = ld_k.labor_cif
    LEFT JOIN district_korea ld_ko ON ld_k.district_id = ld_ko.disk_id
    LEFT JOIN province_korea pk ON ld_k.province_id = pk.province_id
    LEFT JOIN district_korea dk ON ld_k.district_id = dk.disk_id
    LEFT JOIN village_korea vk ON ld_k.village_id = vk.village_id
    LEFT JOIN employer e ON ld_k.employer_id = e.employer_id
    LEFT JOIN quota q ON ld_k.quota_id = q.quota_id
    LEFT JOIN account_korea ak ON ld_k.account_id = ak.account_id
    LEFT JOIN insurance_korea ii ON ld_k.insurance_id = ii.insurance_id
    ORDER BY ld.id DESC
    """
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(q)
        return cur.fetchall()


def _get_labor_department_stats(conn: Connection) -> Dict:
    """Get labor department statistics."""
    q = "SELECT labor_type, COUNT(*) as count FROM labor_department GROUP BY labor_type"
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(q)
        stats = {row["labor_type"]: row["count"] for row in cur.fetchall()}
        return {
            "total": sum(stats.values()),
            "by_type": stats
        }


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