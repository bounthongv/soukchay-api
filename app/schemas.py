"""Pydantic response schemas for the Soukchay API."""

from datetime import date
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

DateLike = Union[str, date]  # PyMySQL: DATE -> date, zero-date '0000-00-00' -> str


class _RowModel(BaseModel):
    """Base for models populated from DB rows: snake_case field names match row
    keys (populate_by_name), JSON output is camelCase (alias_generator)."""

    model_config = ConfigDict(
        populate_by_name=True, alias_generator=to_camel, extra="ignore"
    )


class Worker(_RowModel):
    """A single worker record from data_entry (the 31 requested fields).

    validation_alias = source column; JSON key = camelCase field name.
    """

    cid: Optional[str] = Field(None, validation_alias="data_id")  # data_id -> cid
    cif: Optional[str] = None  # cif
    eng_name: Optional[str] = Field(None, validation_alias="la_eng_name")  # -> engName
    eng_surname: Optional[str] = Field(
        None, validation_alias="surname"
    )  # -> engSurname
    lao_name: Optional[str] = Field(None, validation_alias="la_lao_name")  # -> laoName
    lao_surname: Optional[str] = Field(
        None, validation_alias="la_lao_sure"
    )  # -> laoSurname
    phone_no: Optional[str] = Field(None, validation_alias="la_phone_no")  # -> phoneNo
    phone_no2: Optional[str] = Field(
        None, validation_alias="la_phone_no2"
    )  # -> phoneNo2
    fam_phone_no: Optional[str] = Field(
        None, validation_alias="la_fam_phone"
    )  # -> famPhoneNo
    date_of_birth: Optional[DateLike] = Field(
        None, validation_alias="la_dob"
    )  # -> dateOfBirth
    age: Optional[int] = Field(None, validation_alias="la_age")
    gender: Optional[str] = Field(None, validation_alias="la_gender")
    nationality: Optional[str] = Field(None, validation_alias="la_nationality")
    village: Optional[str] = Field(None, validation_alias="la_vill_lao")
    district: Optional[str] = Field(None, validation_alias="la_dis_lao")
    province: Optional[str] = Field(None, validation_alias="la_pro_lao")
    eng_village: Optional[str] = Field(
        None, validation_alias="la_vill"
    )  # -> engVillage
    eng_district: Optional[str] = Field(
        None, validation_alias="la_dis"
    )  # -> engDistrict
    eng_province: Optional[str] = Field(
        None, validation_alias="la_pro"
    )  # -> engProvince
    weight: Optional[str] = None  # weight
    height: Optional[str] = None  # height
    passport_no: Optional[str] = Field(None, validation_alias="la_kyc")  # -> passportNo
    passport_issue_date: Optional[DateLike] = Field(
        None, validation_alias="la_fist_date_kyc"
    )  # -> passportIssueDate
    passport_exp_date: Optional[DateLike] = Field(
        None, validation_alias="la_exp_date_kyc"
    )  # -> passportExpDate
    labor_type: Optional[str] = None  # labor_department.labor_type -> laborType
    heal_date: Optional[DateLike] = None  # heal_date
    heal_remark: Optional[str] = None  # heal_remark (pass/not pass)
    diagnose: Optional[str] = None  # diagnose
    labour_fee: Optional[float] = Field(
        None, validation_alias="check_up"
    )  # -> labourFee
    health_check_fee: Optional[float] = Field(
        None, validation_alias="check_up2"
    )  # -> healthCheckFee
    status: Optional[str] = None  # data_entry.status
    # extra useful for the app
    date_create: Optional[DateLike] = None  # date_create -> dateCreate
    unit: Optional[str] = Field(None, validation_alias="la_unit")  # -> unit


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


class WorkerStats(_RowModel):
    """GET /workers/stats — counts grouped by data_entry.status."""

    total: int
    by_status: Dict[str, int] = Field(default_factory=dict)  # status -> count


class LaborDepartment(_RowModel):
    """A labor_department record (docs/1 §2 — 22 requested fields)."""

    labor_id: Optional[int] = None  # PK
    data_id: Optional[str] = None
    labor_cif: Optional[str] = None
    status: Optional[int] = Field(
        None, validation_alias="sts_loan"
    )  # labor_department.sts_loan
    labor_type: Optional[str] = None
    visa_ex_date: Optional[DateLike] = None
    order_date: Optional[DateLike] = None
    labor_follow_visa: Optional[str] = None
    travel: Optional[str] = None
    labor_season: Optional[str] = None
    labor_remark: Optional[str] = None
    quota_month: Optional[str] = None
    quota_year: Optional[str] = None
    # joined: data_entry — CCVI/VISA workflow + bank accounts
    ccvi_sub_date: Optional[DateLike] = None
    ccvi_is_date: Optional[DateLike] = None
    visa_sub_date: Optional[DateLike] = None
    ccvi_visa_date: Optional[DateLike] = None
    dep_date: Optional[DateLike] = None
    due_date: Optional[DateLike] = None
    bank_acc_no: Optional[str] = None
    bank_acc_no2: Optional[str] = None
    # joined: Korea lookups
    employer: Optional[str] = Field(
        None, validation_alias="employer_name"
    )  # employer_name
    disk_code: Optional[str] = None  # district_korea.disk_code
    korea_province_eng: Optional[str] = None
    korea_district_eng: Optional[str] = None
    korea_province_lao: Optional[str] = None
    korea_district_lao: Optional[str] = None


class LaborDepartmentStats(_RowModel):
    """GET /labor-department/stats — counts grouped by labor_type."""

    total: int
    by_type: Dict[str, int] = Field(default_factory=dict)  # labor_type -> count


class LoanDepartmentStats(_RowModel):
    """GET /loan-department/stats — counts grouped by sts_insert."""

    total: int
    by_status: Dict[str, int] = Field(default_factory=dict)  # status -> count


class FaDepartmentStats(_RowModel):
    """GET /fa-department/stats — counts grouped by status."""

    total: int
    by_status: Dict[str, int] = Field(default_factory=dict)  # status -> count


class LoanDepartment(_RowModel):
    """A loan_department record (docs/1 §3 + computed interest fields)."""

    loan_id: Optional[int] = None  # PK
    cif: Optional[str] = None
    status: Optional[str] = Field(None, validation_alias="sts_insert")  # sts_insert
    fin_price: Optional[float] = None  # decimal
    rate: Optional[str] = None  # e.g. '1.2%'
    term: Optional[str] = None
    first_due_date: Optional[DateLike] = None
    last_due_date: Optional[DateLike] = None
    ex_rate: Optional[str] = None  # varchar, e.g. '22500'
    price1: Optional[float] = None  # Labour fee
    price2: Optional[float] = None  # Upfront fee
    price3: Optional[float] = None  # Installment in Advance (interest in advance)
    price4: Optional[float] = None  # Total debt
    price5: Optional[float] = None  # Labour balance
    sts_close: Optional[str] = None
    # joined: data_entry person + address
    la_name: Optional[str] = Field(None, validation_alias="la_eng_name")  # la_eng_name
    surname: Optional[str] = None
    la_lao_name: Optional[str] = None
    la_lao_sure: Optional[str] = None
    province_lao: Optional[str] = None
    province: Optional[str] = None
    district_lao: Optional[str] = None
    district: Optional[str] = None
    village_lao: Optional[str] = None
    village: Optional[str] = None
    # computed (services/interest.py)
    days_overdue: Optional[int] = None
    elapsed_term_days: Optional[int] = None
    interest_payable: Optional[float] = None
    over_under_amount: Optional[float] = None


class FaDepartment(_RowModel):
    """An fa_department record (docs/1 §4 — loan join + computed fields)."""

    fa_id: Optional[int] = None  # PK
    cif: Optional[str] = None
    status: Optional[str] = None  # fa_department.status
    type_play: Optional[int] = None
    sc_group: Optional[str] = None
    sts_close: Optional[str] = None
    # joined: loan_department
    fin_price: Optional[float] = None
    rate: Optional[str] = None
    term: Optional[str] = None
    first_due_date: Optional[DateLike] = None
    last_due_date: Optional[DateLike] = None
    ex_rate: Optional[str] = None
    price4: Optional[float] = None  # loan price4 — total debt
    # joined: data_entry person + address
    la_name: Optional[str] = Field(None, validation_alias="la_eng_name")  # la_eng_name
    surname: Optional[str] = None
    la_lao_name: Optional[str] = None
    la_lao_sure: Optional[str] = None
    province_lao: Optional[str] = None
    province: Optional[str] = None
    district_lao: Optional[str] = None
    district: Optional[str] = None
    village_lao: Optional[str] = None
    village: Optional[str] = None
    # computed (services/interest.py)
    days_overdue: Optional[int] = None
    elapsed_term_days: Optional[int] = None
    interest_payable: Optional[float] = None
    over_under_amount: Optional[float] = None
    total_debt_lak: Optional[float] = None
    total_debt_usd: Optional[float] = None


class LaborFollowUp(_RowModel):
    """A labor_follow_korea record (docs/1 §5 — 21 requested fields).

    Three requested rows (Return Date, Return Laos (run away), Early Return
    Date) all read the same labor_follow_korea.return_date column — hence the
    shared validation_alias.
    """

    fol_id: Optional[int] = None  # PK
    data_id: Optional[str] = None
    cif: Optional[str] = None
    code: Optional[str] = None
    status: Optional[str] = Field(None, validation_alias="sts_follow")  # sts_follow
    status_payment: Optional[str] = Field(
        None, validation_alias="sts_close"
    )  # sts_close
    enter_center: Optional[str] = Field(
        None, validation_alias="fa_in_soun"
    )  # fa_in_soun
    time_extension: Optional[str] = Field(None, validation_alias="time_ex")  # time_ex
    price_extension: Optional[str] = Field(
        None, validation_alias="price_ex"
    )  # price_ex
    visa_extension_from_date: Optional[DateLike] = Field(
        None, validation_alias="visa_form_date"
    )  # visa_form_date
    visa_extension_to_date: Optional[DateLike] = Field(
        None, validation_alias="visa_to_date"
    )  # visa_to_date
    return_date: Optional[DateLike] = None
    return_laos_run_away: Optional[DateLike] = Field(
        None, validation_alias="return_date"
    )  # return_date
    early_return_date: Optional[DateLike] = Field(
        None, validation_alias="return_date"
    )  # return_date
    run_away_date: Optional[DateLike] = Field(
        None, validation_alias="run_date"
    )  # run_date
    date_received_notice: Optional[DateLike] = Field(
        None, validation_alias="date_kam"
    )  # date_kam
    return_to_korea: Optional[str] = Field(
        None, validation_alias="return_korea"
    )  # return_korea
    month_returned: Optional[str] = Field(
        None, validation_alias="fol_month"
    )  # fol_month
    year_returned: Optional[str] = Field(None, validation_alias="fol_year")  # fol_year
    reason_return_korea: Optional[str] = Field(
        None, validation_alias="re_korea"
    )  # re_korea
    remark: Optional[str] = None
    remark_run_away: Optional[str] = Field(None, validation_alias="remark2")  # remark2
    remark_early_return: Optional[str] = Field(
        None, validation_alias="early_remark"
    )  # early_remark
    remark_blacklist: Optional[str] = Field(
        None, validation_alias="blacklist_remark"
    )  # blacklist_remark
    blacklist_date: Optional[DateLike] = None
    visa_ex_date: Optional[DateLike] = None
    fol_date: Optional[DateLike] = None
    # joined: labor_department + Korea lookups
    labor_type: Optional[str] = None
    labor_name: Optional[str] = None
    labor_name_lao: Optional[str] = None
    employer: Optional[str] = Field(
        None, validation_alias="employer_name"
    )  # employer_name
    korea_province_eng: Optional[str] = None
    korea_district_eng: Optional[str] = None
    korea_province_lao: Optional[str] = None
    korea_district_lao: Optional[str] = None
    # joined: data_entry person + address
    la_name: Optional[str] = Field(None, validation_alias="la_eng_name")  # la_eng_name
    surname: Optional[str] = None
    la_lao_name: Optional[str] = None
    la_lao_sure: Optional[str] = None
    province_lao: Optional[str] = None
    province: Optional[str] = None
    district_lao: Optional[str] = None
    district: Optional[str] = None
    village_lao: Optional[str] = None
    village: Optional[str] = None


class LaborFollowUpStats(_RowModel):
    """GET /follow-up/stats — counts grouped by fa_in_soun."""

    total: int
    by_status: Dict[str, int] = Field(default_factory=dict)  # fa_in_soun -> count
