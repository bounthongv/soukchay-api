"""Labor Follow-up endpoint for the Soukchay API.

Provides labor follow-up records with Korean placement details and statistics.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pymysql import Connection

from ..db import get_conn
from ..schemas import LaborFollowUp, LaborFollowUpStats
from ..auth import require_api_key


router = APIRouter(prefix="/follow-up", tags=["Labor Follow-up"], dependencies=[Depends(require_api_key)])


def _get_labor_follow_up(conn: Connection, follow_id: int) -> Optional[Dict]:
    """Fetch a single labor follow-up record with Korean details."""
    q = """
    SELECT 
        lf.*,
        ld.labor_type,
        de.la_eng_name, de.surname, de.la_lao_name, de.la_lao_sure,
        de.emp_name AS employer_name,
        dk.disk_code,
        dk.disk_name_lao AS korea_district_lao,
        dk.disk_name AS korea_district_eng,
        pk.prok_name AS korea_province_lao,
        pk.prok_name AS korea_province_eng,
        p.pro_name_lao AS province_lao, p.pro_name AS province,
        d.dis_name_lao AS district_lao, d.dis_name AS district,
        v.vill_name_lao AS village_lao, v.vill_name AS village
    FROM labor_follow_korea lf
    LEFT JOIN (
        SELECT cif, MAX(id) AS id
        FROM data_entry GROUP BY cif
    ) demax ON demax.cif = lf.cif
    LEFT JOIN data_entry de ON de.id = demax.id
    LEFT JOIN (
        SELECT data_id, MAX(labor_id) AS labor_id
        FROM labor_department GROUP BY data_id
    ) ldmax ON ldmax.data_id = de.data_id
    LEFT JOIN labor_department ld ON ld.labor_id = ldmax.labor_id
    LEFT JOIN district_korea dk ON LPAD(TRIM(de.emp_dis), 5, '0') = dk.disk_id
    LEFT JOIN province_korea pk ON dk.prok_id = pk.prok_id
    LEFT JOIN province p ON de.la_pro = p.pro_id
    LEFT JOIN district d ON de.la_dis = d.dis_id
    LEFT JOIN village v ON de.la_vill = v.vill_id
    WHERE lf.fol_id = %s
    """
    with conn.cursor() as cur:
        cur.execute(q, (follow_id,))
        return cur.fetchone()


def _get_labor_follow_up_list(conn: Connection) -> List[Dict]:
    """Fetch all labor follow-up records."""
    q = """
    SELECT 
        lf.*,
        ld.labor_type,
        de.la_eng_name, de.surname, de.la_lao_name, de.la_lao_sure,
        de.emp_name AS employer_name,
        dk.disk_code,
        dk.disk_name_lao AS korea_district_lao,
        dk.disk_name AS korea_district_eng,
        pk.prok_name AS korea_province_lao,
        pk.prok_name AS korea_province_eng,
        p.pro_name_lao AS province_lao, p.pro_name AS province,
        d.dis_name_lao AS district_lao, d.dis_name AS district,
        v.vill_name_lao AS village_lao, v.vill_name AS village
    FROM labor_follow_korea lf
    LEFT JOIN (
        SELECT cif, MAX(id) AS id
        FROM data_entry GROUP BY cif
    ) demax ON demax.cif = lf.cif
    LEFT JOIN data_entry de ON de.id = demax.id
    LEFT JOIN (
        SELECT data_id, MAX(labor_id) AS labor_id
        FROM labor_department GROUP BY data_id
    ) ldmax ON ldmax.data_id = de.data_id
    LEFT JOIN labor_department ld ON ld.labor_id = ldmax.labor_id
    LEFT JOIN district_korea dk ON LPAD(TRIM(de.emp_dis), 5, '0') = dk.disk_id
    LEFT JOIN province_korea pk ON dk.prok_id = pk.prok_id
    LEFT JOIN province p ON de.la_pro = p.pro_id
    LEFT JOIN district d ON de.la_dis = d.dis_id
    LEFT JOIN village v ON de.la_vill = v.vill_id
    ORDER BY lf.fol_id DESC
    """
    with conn.cursor() as cur:
        cur.execute(q)
        return cur.fetchall()


def _get_labor_follow_up_stats(conn: Connection) -> Dict:
    """Get labor follow-up statistics."""
    q = "SELECT fa_in_soun, COUNT(*) as count FROM labor_follow_korea GROUP BY fa_in_soun"
    with conn.cursor() as cur:
        cur.execute(q)
        stats = {row["fa_in_soun"]: row["count"] for row in cur.fetchall()}
        return {"total": sum(stats.values()), "by_status": stats}


@router.get("", response_model=List[LaborFollowUp])
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
