from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from . import models, schemas
from .dependencies import get_current_user

router = APIRouter(prefix="/expenses", tags=["Expenses"])


# ADD EXPENSE (SECURED)
@router.post("/", response_model=schemas.ExpenseResponse)
def add_expense(
    expense: schemas.ExpenseCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):

    new_expense = models.Expense(
        amount=expense.amount,
        category=expense.category,
        description=expense.description,
        expense_date=expense.expense_date,
        owner_id=user.id
    )

    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)

    return new_expense


# GET MY EXPENSES (SECURED)
@router.get("/me", response_model=List[schemas.ExpenseResponse])
def get_my_expenses(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):

    expenses = db.query(models.Expense).filter(
        models.Expense.owner_id == user.id
    ).all()

    return expenses


# DELETE EXPENSE (SECURED)
@router.delete("/{expense_id}")
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):

    expense = db.query(models.Expense).filter(
        models.Expense.id == expense_id
    ).first()

    if not expense:
        raise HTTPException(
            status_code=404,
            detail="Expense not found"
        )

    if expense.owner_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to delete this expense"
        )

    db.delete(expense)
    db.commit()

    return {"message": "Expense deleted"}