from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class UserCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)


class UserCategoryCreate(UserCategoryBase):
    pass


class UserCategoryUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)


class UserCategoryOut(UserCategoryBase):
    id: int

    model_config = {"from_attributes": True}


class UserTypeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)


class UserTypeCreate(UserTypeBase):
    pass


class UserTypeUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)


class UserTypeOut(UserTypeBase):
    id: int

    model_config = {"from_attributes": True}


class UserBase(BaseModel):
    phone_number: Optional[str] = Field(None, max_length=20)
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    category_id: Optional[int] = None


class UserCreate(UserBase):
    @field_validator("phone_number")
    @classmethod
    def phone_must_have_digits(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            digits = "".join(c for c in v if c.isdigit())
            if len(digits) < 9:
                raise ValueError("Phone number must contain at least 9 digits")
        return v


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    category_id: Optional[int] = None
    type_ids: Optional[List[int]] = None


class UserOut(UserBase):
    id: int
    calls_count: int
    created_at: datetime
    updated_at: datetime
    category: Optional[UserCategoryOut] = None
    types: List[UserTypeOut] = []

    model_config = {"from_attributes": True}


class UserListOut(BaseModel):
    """Lightweight user representation for list endpoints."""
    id: int
    phone_number: Optional[str]
    name: Optional[str]
    calls_count: int
    category: Optional[UserCategoryOut] = None
    types: List[UserTypeOut] = []

    model_config = {"from_attributes": True}
