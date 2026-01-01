from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from uuid import UUID


# ============================================
# A. 컬럼 수 비교 스키마
# ============================================
class UserNarrowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    status: str
    created_at: datetime


class UserWideResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    status: str
    created_at: datetime
    phone: str | None
    address: str | None
    city: str | None
    country: str | None
    postal_code: str | None
    birth_date: date | None
    gender: str | None
    occupation: str | None
    company: str | None
    website: str | None
    bio: str | None
    avatar_url: str | None
    last_login: datetime | None
    login_count: int
    preferences: dict | None


class UserExtraWideResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    field_01: str | None
    field_02: str | None
    field_03: str | None
    field_04: str | None
    field_05: str | None
    field_06: str | None
    field_07: str | None
    field_08: str | None
    field_09: str | None
    field_10: str | None
    field_11: str | None
    field_12: str | None
    field_13: str | None
    field_14: str | None
    field_15: str | None
    field_16: str | None
    field_17: str | None
    field_18: str | None
    field_19: str | None
    field_20: str | None
    field_21: str | None
    field_22: str | None
    field_23: str | None
    field_24: str | None
    field_25: str | None
    field_26: str | None
    field_27: str | None
    field_28: str | None
    field_29: str | None
    field_30: str | None
    field_31: str | None
    field_32: str | None
    field_33: str | None
    field_34: str | None
    field_35: str | None
    field_36: str | None
    field_37: str | None
    field_38: str | None
    field_39: str | None
    field_40: str | None
    field_41: str | None
    field_42: str | None
    field_43: str | None
    field_44: str | None
    field_45: str | None
    created_at: datetime


# ============================================
# B. 데이터 타입별 비교 스키마
# ============================================


class UserTypeIntResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    int_col_01: int
    int_col_02: int
    int_col_03: int
    int_col_04: int
    int_col_05: int


class UserTypeVarcharResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    varchar_col_01: str | None
    varchar_col_02: str | None
    varchar_col_03: str | None
    varchar_col_04: str | None
    varchar_col_05: str | None


class UserTypeTextResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    text_col_01: str | None
    text_col_02: str | None
    text_col_03: str | None
    text_col_04: str | None
    text_col_05: str | None


class UserTypeJsonbResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    json_col_01: dict | None
    json_col_02: dict | None
    json_col_03: dict | None
    json_col_04: dict | None
    json_col_05: dict | None


class UserTypeTimestampResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    ts_col_01: datetime | None
    ts_col_02: datetime | None
    ts_col_03: datetime | None
    ts_col_04: datetime | None
    ts_col_05: datetime | None


class UserTypeUuidResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    uuid_col_01: UUID | None
    uuid_col_02: UUID | None
    uuid_col_03: UUID | None
    uuid_col_04: UUID | None
    uuid_col_05: UUID | None
