from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import tempfile
from pathlib import Path

from .database import get_db
from . import models
from .dependencies import get_current_user

from fastapi.responses import FileResponse

from ui.pdf_reports import generate_pdf


router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/budget-alert/{limit}")
def budget_alert(
    limit: float,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):

    expenses = db.query(models.Expense).filter(
        models.Expense.owner_id == user.id
    ).all()

    total = sum(e.amount for e in expenses)

    if total > limit:
        return {
            "alert": "⚠ Budget exceeded!",
            "spent": total,
            "limit": limit
        }

    return {
        "message": "Within budget",
        "spent": total,
        "remaining": limit - total
    }


@router.get("/download-pdf")
def download_pdf(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):

    expenses = db.query(models.Expense).filter(
        models.Expense.owner_id == user.id
    ).all()

    file_path = generate_pdf(expenses)

    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename="expense_report.pdf"
    )


# ==============================
# MONTHLY REPORT DATA
# ==============================
@router.get("/monthly")
def monthly_report(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):

    expenses = db.query(models.Expense).filter(
        models.Expense.owner_id == user.id
    ).all()

    data = []

    for e in expenses:
        data.append({
            "date": e.expense_date,
            "amount": e.amount
        })

    df = pd.DataFrame(data)

    if df.empty:
        return {"message": "No data available"}

    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)

    result = df.groupby("month")["amount"].sum().reset_index()

    return result.to_dict(orient="records")


@router.get("/category-chart")
def category_chart(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):

    expenses = db.query(models.Expense).filter(
        models.Expense.owner_id == user.id
    ).all()

    if not expenses:
        return {"message": "No data"}

    categories = {}

    for e in expenses:
        categories[e.category] = categories.get(e.category, 0) + e.amount

    labels = list(categories.keys())
    values = list(categories.values())

    plt.figure(figsize=(6, 6))
    plt.pie(values, labels=labels, autopct="%1.1f%%")
    plt.title("Expense by Category")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        file_path = tmp.name

    plt.savefig(file_path, bbox_inches="tight")
    plt.close()

    return FileResponse(
        file_path,
        media_type="image/png",
        filename="category_chart.png"
    )


@router.get("/monthly-chart")
def monthly_chart(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):

    expenses = db.query(models.Expense).filter(
        models.Expense.owner_id == user.id
    ).all()

    if not expenses:
        return {"message": "No data"}

    data = []

    for e in expenses:
        data.append({
            "date": e.expense_date,
            "amount": e.amount
        })

    df = pd.DataFrame(data)

    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)

    grouped = df.groupby("month")["amount"].sum()

    plt.figure(figsize=(8, 5))
    grouped.plot(kind="bar")

    plt.title("Monthly Expenses")
    plt.xlabel("Month")
    plt.ylabel("Amount")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        file_path = tmp.name

    plt.savefig(file_path, bbox_inches="tight")
    plt.close()

    return FileResponse(
        file_path,
        media_type="image/png",
        filename="monthly_chart.png"
    )