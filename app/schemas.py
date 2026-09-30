"""Pydantic response schemas for the Soukchay API."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class Worker(BaseModel):
    """A single worker record from data_entry (the 31 requested fields)."""
    cid: Optional[str] = None            # data_id
    cif: Optional[str] = None            # cif
    engName: Optional[str] = None        # la_eng_name
    engSurname: Optional[str] = None     # surname
    laoName: Optional[str] = None        # la_lao_name
    laoSurname: Optional[str] = None     # la_lao_sure
    phoneNo: Optional[str] = None        # la_phone_no
    phoneNo2: Optional[str] = None       # la_phone_no2
    famPhoneNo: Optional[str] = None     # la_fam_phone
    dateOfBirth: Optional[str] = None    # la_dob
    age: Optional[int] = None            # la_age
    gender: Optional[str] = None         # la_gender
    nationality: Optional[str] = None    # la_nationality
    village: Optional[str] = None        # la_vill_lao
    district: Optional[str] = None       # la_dis_lao
    province: Optional[str] = None       # la_pro_lao
    engVillage: Optional[str] = None     # la_vill
    engDistrict: Optional[str] = None    # la_dis
    engProvince: Optional[str] = None    # la_pro
    weight: Optional[str] = None         # weight
    height: Optional[str] = None         # height
    passportNo: Optional[str] = None     # la_kyc
    passportIssueDate: Optional[str] = None  # la_fist_date_kyc
    passportExpDate: Optional[str] = None    # la_exp_date_kyc
    laborType: Optional[str] = None      # labor_department.labor_type
    healDate: Optional[str] = None       # heal_date
    healRemark: Optional[str] = None     # heal_remark (pass/not pass)
    diagnose: Optional[str] = None       # diagnose
    labourFee: Optional[float] = None    # check_up
    healthCheckFee: Optional[float] = None  # check_up2
    status: Optional[str] = None         # data_entry.status
    # extra useful for the app
    dateCreate: Optional[str] = None     # date_create
    unit: Optional[str] = None           # la_unit


class WorkerDetail(Worker):
    """Worker + joined labor/loan/fa/follow-up records."""
    labor: Optional[Dict[str, Any]] = None
    loan: Optional[Dict[str, Any]] = None
    fa: Optional[Dict[str, Any]] = None
    followUp: Optional[Dict[str, Any]] = None
    payments: Optional[List[Dict[str, Any]]] = None


class StatusCount(BaseModel):
    status: str
    count: int


class Stats(BaseModel):
    area: str
    total: int
    byStatus: List[StatusCount]