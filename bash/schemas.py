from pydantic import BaseModel
from datetime import date


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ExpenseCreate(BaseModel):
    amount: float
    category: str
    description: str
    expense_date: date


class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True


class ExpenseResponse(BaseModel):
    id: int
    amount: float
    category: str
    description: str
    expense_date: date

    class Config:
        from_attributes = True