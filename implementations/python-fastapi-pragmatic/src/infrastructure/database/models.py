from sqlalchemy import String, Integer, Text, Date, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from datetime import datetime, date
from sqlalchemy.sql import func
import uuid


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


# ============================================
# A. 컬럼 수 비교 모델
# ============================================
class UserNarrowModel(Base):
    __tablename__ = "users_narrow"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class UserWideModel(Base):
    __tablename__ = "users_wide"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    phone: Mapped[str | None] = mapped_column(String(20))
    address: Mapped[str | None] = mapped_column(String(500))
    city: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    postal_code: Mapped[str | None] = mapped_column(String(20))
    birth_date: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(String(10))
    occupation: Mapped[str | None] = mapped_column(String(100))
    company: Mapped[str | None] = mapped_column(String(200))
    website: Mapped[str | None] = mapped_column(String(255))
    bio: Mapped[str | None] = mapped_column(Text)
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    last_login: Mapped[datetime | None] = mapped_column(DateTime)
    login_count: Mapped[int] = mapped_column(Integer, default=0)
    preferences: Mapped[dict | None] = mapped_column(JSONB, default={})


class UserExtraWideModel(Base):
    __tablename__ = "users_extra_wide"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    field_01: Mapped[str | None] = mapped_column(String(100))
    field_02: Mapped[str | None] = mapped_column(String(100))
    field_03: Mapped[str | None] = mapped_column(String(100))
    field_04: Mapped[str | None] = mapped_column(String(100))
    field_05: Mapped[str | None] = mapped_column(String(100))
    field_06: Mapped[str | None] = mapped_column(String(100))
    field_07: Mapped[str | None] = mapped_column(String(100))
    field_08: Mapped[str | None] = mapped_column(String(100))
    field_09: Mapped[str | None] = mapped_column(String(100))
    field_10: Mapped[str | None] = mapped_column(String(100))
    field_11: Mapped[str | None] = mapped_column(String(100))
    field_12: Mapped[str | None] = mapped_column(String(100))
    field_13: Mapped[str | None] = mapped_column(String(100))
    field_14: Mapped[str | None] = mapped_column(String(100))
    field_15: Mapped[str | None] = mapped_column(String(100))
    field_16: Mapped[str | None] = mapped_column(String(100))
    field_17: Mapped[str | None] = mapped_column(String(100))
    field_18: Mapped[str | None] = mapped_column(String(100))
    field_19: Mapped[str | None] = mapped_column(String(100))
    field_20: Mapped[str | None] = mapped_column(String(100))
    field_21: Mapped[str | None] = mapped_column(String(100))
    field_22: Mapped[str | None] = mapped_column(String(100))
    field_23: Mapped[str | None] = mapped_column(String(100))
    field_24: Mapped[str | None] = mapped_column(String(100))
    field_25: Mapped[str | None] = mapped_column(String(100))
    field_26: Mapped[str | None] = mapped_column(String(100))
    field_27: Mapped[str | None] = mapped_column(String(100))
    field_28: Mapped[str | None] = mapped_column(String(100))
    field_29: Mapped[str | None] = mapped_column(String(100))
    field_30: Mapped[str | None] = mapped_column(String(100))
    field_31: Mapped[str | None] = mapped_column(String(100))
    field_32: Mapped[str | None] = mapped_column(String(100))
    field_33: Mapped[str | None] = mapped_column(String(100))
    field_34: Mapped[str | None] = mapped_column(String(100))
    field_35: Mapped[str | None] = mapped_column(String(100))
    field_36: Mapped[str | None] = mapped_column(String(100))
    field_37: Mapped[str | None] = mapped_column(String(100))
    field_38: Mapped[str | None] = mapped_column(String(100))
    field_39: Mapped[str | None] = mapped_column(String(100))
    field_40: Mapped[str | None] = mapped_column(String(100))
    field_41: Mapped[str | None] = mapped_column(String(100))
    field_42: Mapped[str | None] = mapped_column(String(100))
    field_43: Mapped[str | None] = mapped_column(String(100))
    field_44: Mapped[str | None] = mapped_column(String(100))
    field_45: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


# ============================================
# B. 데이터 타입별 비교 모델
# ============================================
class UserTypeIntModel(Base):
    __tablename__ = "users_type_int"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    int_col_01: Mapped[int] = mapped_column(Integer, default=0)
    int_col_02: Mapped[int] = mapped_column(Integer, default=0)
    int_col_03: Mapped[int] = mapped_column(Integer, default=0)
    int_col_04: Mapped[int] = mapped_column(Integer, default=0)
    int_col_05: Mapped[int] = mapped_column(Integer, default=0)


class UserTypeVarcharModel(Base):
    __tablename__ = "users_type_varchar"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    varchar_col_01: Mapped[str | None] = mapped_column(String(100))
    varchar_col_02: Mapped[str | None] = mapped_column(String(100))
    varchar_col_03: Mapped[str | None] = mapped_column(String(100))
    varchar_col_04: Mapped[str | None] = mapped_column(String(100))
    varchar_col_05: Mapped[str | None] = mapped_column(String(100))


class UserTypeTextModel(Base):
    __tablename__ = "users_type_text"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    text_col_01: Mapped[str | None] = mapped_column(Text)
    text_col_02: Mapped[str | None] = mapped_column(Text)
    text_col_03: Mapped[str | None] = mapped_column(Text)
    text_col_04: Mapped[str | None] = mapped_column(Text)
    text_col_05: Mapped[str | None] = mapped_column(Text)


class UserTypeJsonbModel(Base):
    __tablename__ = "users_type_jsonb"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    json_col_01: Mapped[dict | None] = mapped_column(JSONB, default={})
    json_col_02: Mapped[dict | None] = mapped_column(JSONB, default={})
    json_col_03: Mapped[dict | None] = mapped_column(JSONB, default={})
    json_col_04: Mapped[dict | None] = mapped_column(JSONB, default={})
    json_col_05: Mapped[dict | None] = mapped_column(JSONB, default={})


class UserTypeTimestampModel(Base):
    __tablename__ = "users_type_timestamp"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    ts_col_01: Mapped[datetime | None] = mapped_column(DateTime)
    ts_col_02: Mapped[datetime | None] = mapped_column(DateTime)
    ts_col_03: Mapped[datetime | None] = mapped_column(DateTime)
    ts_col_04: Mapped[datetime | None] = mapped_column(DateTime)
    ts_col_05: Mapped[datetime | None] = mapped_column(DateTime)


class UserTypeUuidModel(Base):
    __tablename__ = "users_type_uuid"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    uuid_col_01: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    uuid_col_02: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    uuid_col_03: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    uuid_col_04: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    uuid_col_05: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
