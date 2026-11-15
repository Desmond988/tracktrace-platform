import re
import uuid
from datetime import UTC, datetime
from typing import Annotated, Generic, TypeVar

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, EmailStr

T = TypeVar("T")
PHONE_RE = re.compile(r"^[+0-9 ()\-.]{6,25}$")


def _strip(v):
    return v.strip() if isinstance(v, str) else v


def _empty_to_none(v):
    v = _strip(v)
    return None if v == "" else v


def _phone(v: str | None) -> str | None:
    if v is None:
        return v
    if not PHONE_RE.match(v):
        raise ValueError("Invalid phone number")
    return v


def _aware(v: datetime | None) -> datetime | None:
    if v is not None and v.tzinfo is None:
        return v.replace(tzinfo=UTC)
    return v


Str = Annotated[str, BeforeValidator(_strip)]
OptStr = Annotated[str | None, BeforeValidator(_empty_to_none)]
Phone = Annotated[str | None, BeforeValidator(_empty_to_none), AfterValidator(_phone)]
OptEmail = Annotated[EmailStr | None, BeforeValidator(_empty_to_none)]
AwareDT = Annotated[datetime | None, AfterValidator(_aware)]


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class Msg(BaseModel):
    message: str


class StatusOut(ORM):
    code: str
    label: dict[str, str]
    sort_order: int
    is_terminal: bool
    is_problem: bool
    is_active: bool
    notify_customer: bool


class ServiceOut(ORM):
    id: uuid.UUID
    code: str
    name: dict[str, str]
    is_active: bool
    sort_order: int
