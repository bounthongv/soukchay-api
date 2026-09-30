"""Labor Follow-up endpoint for the Soukchay API.

Provides labor follow-up records with Korean placement details and statistics.
"""
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pymysql import Connection

from ...db import get_conn
from ...schemas import LaborFollowUp, LaborFollowUpStats


router = APIRouter(prefix="/follow-up", tags=["Labor Follow-up"])


def _get_labor_follow_up(conn: Connection, follow_id: int) -> Optional[Dict]:
    """Fetch a single labor follow-up record with Korean details."""
    q = """
    SELECT 
        lf.*,
        ld.labor_type,
        ld_k.labor_name, ld_k.labor_name_lao,
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
        ii.insurance_name, ii.insurance_name_lao,
        de.la_name, de.surname, de.la_lao_name, de.la_lao_sure,
        p.province_lao, p.province,
        d.district_lao, d.district,
        v.village_lao, v.village
    FROM labor_follow_korea lf
    LEFT JOIN labor_department ld ON lf.cif = ld.cif
    LEFT JOIN labor_department_korea ld_k ON ld.labor_cif = ld_k.labor_cif
    LEFT JOIN district_korea ld_ko ON ld_k.district_id = ld_ko.disk_id
    LEFT JOIN province_korea pk ON ld_k.province_id = pk.province_id
    LEFT JOIN district_korea dk ON ld_k.district_id = dk.disk_id
    LEFT JOIN village_korea vk ON ld_k.village_id = vk.village_id
    LEFT JOIN employer e ON ld_k.employer_id = e.employer_id
    LEFT JOIN quota q ON ld_k.quota_id = q.quota_id
    LEFT JOIN account_korea ak ON ld_k.account_id = ak.account_id
    LEFT JOIN insurance_korea ii ON ld_k.insurance_id = ii.insurance_id
    LEFT JOIN data_entry de ON lf.cif = de.cif
    LEFT JOIN province p ON de.la_pro = p.province_id
    LEFT JOIN district d ON de.la_dis = d.district_id
    LEFT JOIN village v ON de.la_vill = v.village_id
    WHERE lf.id = %s
    """
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(q, (follow_id,))
        return cur.fetchone()


def _get_labor_follow_up_list(conn: Connection) -> List[Dict]:
    """Fetch all labor follow-up records."""
    q = """
    SELECT 
        lf.*,
        ld.labor_type,
        ld_k.labor_name, ld_k.labor_name_lao,
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
        ii.insurance_name, ii.insurance_name_lao,
        de.la_name, de.surname, de.la_lao_name, de.la_lao_sure,
        p.province_lao, p.province,
        d.district_lao, d.district,
        v.village_lao, v.village
    FROM labor_follow_korea lf
    LEFT JOIN labor_department ld ON lf.cif = ld.cif
    LEFT JOIN labor_department_korea ld_k ON ld.labor_cif = ld_k.labor_cif
    LEFT JOIN district_korea ld_ko ON ld_k.district_id = ld_ko.disk_id
    LEFT JOIN province_korea pk ON ld_k.province_id = pk.province_id
    LEFT JOIN district_korea dk ON ld_k.district_id = dk.disk_id
    LEFT JOIN village_korea vk ON ld_k.village_id = vk.village_id
    LEFT JOIN employer e ON ld_k.employer_id = e.employer_id
    LEFT JOIN quota q ON ld_k.quota_id = q.quota_id
    LEFT JOIN account_korea ak ON ld_k.account_id = ak.account_id
    LEFT JOIN insurance_korea ii ON ld_k.insurance_id = ii.insurance_id
    LEFT JOIN data_entry de ON lf.cif = de.cif
    LEFT JOIN province p ON de.la_pro = p.province_id
    LEFT JOIN district d ON de.la_dis = d.district_id
    LEFT JOIN village v ON de.la_vill = v.village_id
    ORDER BY lf.id DESC
    """
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(q)
        return cur.fetchall()


def _get_labor_follow_up_stats(conn: Connection) -> Dict:
    """Get labor follow-up statistics."""
    q = "SELECT fa_in_soun, COUNT(*) as count FROM labor_follow_korea GROUP BY fa_in_soun"
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(q)
        stats = {row["fa_in_soun"]: row["count"] for row in cur.fetchall()}
        return {
            "total": sum(stats.values()),
            "by_status": stats
        }


@router.get("", response_model=LaborFollowUp)
def list_labor_follow_up(conn: Connection = Depends(get_conn)):
    """List all labor follow-up records."""
    return _get_labor_follow_up_list(conn)


@router.get("/stats", response_model=LaborFollowUpStats)
def labor_follow_up_stats(conn: Connection = Depends(get_conn)):
    """Get labor follow-up statistics."""
    return _get_labor_follow_up_stats(conn)


@router.get("/{follow_id}", response_model=LaborFollowUp)
def get_labor_follow_up(follow_id: int, conn: Connection = Depends(get_conn)):
    """Get a single labor follow-up record."""
    record = _get_labor_follow_up(conn, follow_id)
    if not record:
        raise HTTPException(status_code=404, detail="Labor follow-up record not found")
    return record