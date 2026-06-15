from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates

from bash.database import SessionLocal
from bash import models, auth
from .pdf_reports import generate_pdf
from .email import send_email

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR))


# =========================
# LOGIN PAGE
# =========================
@router.get("/ui/login", response_class=HTMLResponse)
def login_page(request: Request):
   return templates.TemplateResponse(
    request=request,
    name="login.html"
    
)


# =========================
# LOGIN ACTION
# =========================
@router.post("/ui/login")
def login_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    remember_me: bool = Form(False)
):

    with SessionLocal() as db:
        user = db.query(models.User).filter(
            models.User.username == username
        ).first()

    if not user or not auth.verify_password(password, user.password):
        templates.TemplateResponse(
    request=request,
    name="login.html",
    context={"error": "Invalid credentials"}
)

    access_token = auth.create_access_token({"user_id": user.id})
    refresh_expires = auth.REFRESH_TOKEN_EXPIRE_MINUTES
    if remember_me:
        refresh_expires = auth.REMEMBER_ME_REFRESH_EXPIRE_MINUTES

    refresh_token = auth.create_refresh_token(
        {"user_id": user.id},
        expires_minutes=refresh_expires
    )

    response = RedirectResponse(url="/ui/dashboard", status_code=302)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=auth.COOKIE_TOKEN_MAX_AGE,
        expires=auth.COOKIE_TOKEN_MAX_AGE
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=refresh_expires * 60,
        expires=refresh_expires * 60
    )

    return response


# =========================
# REGISTER PAGE
# =========================
@router.get("/ui/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(
    request=request,
    name="register.html"
)


# =========================
# REGISTER ACTION
# =========================
@router.post("/ui/register")
def register_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)
):

    if password != confirm_password:
       return templates.TemplateResponse(
    request=request,
    name="register.html",
    context={
        "error": "Passwords do not match"
    }
)

    with SessionLocal() as db:
        existing_user = db.query(models.User).filter(
            (models.User.username == username) | (models.User.email == email)
        ).first()

        if existing_user:
            return templates.TemplateResponse(
    request=request,
    name="register.html",
    context={
        "error": "Username or email already registered"
    }
)
        new_user = models.User(
            username=username,
            email=email,
            password=auth.hash_password(password)
        )

        db.add(new_user)
        db.commit()

    return templates.TemplateResponse(
    request=request,
    name="register.html",
    context={
        "success": "Account created successfully. You can now log in."
    }
)


# =========================
# REFRESH SESSION
# =========================
@router.get("/ui/refresh")
def refresh_session(request: Request):
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        return RedirectResponse("/ui/login")

    user_id = auth.verify_refresh_token(refresh_token)

    if not user_id:
        response = RedirectResponse("/ui/login")
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response

    access_token = auth.create_access_token({"user_id": user_id})
    new_refresh_token = auth.create_refresh_token({"user_id": user_id})

    response = RedirectResponse(url="/ui/dashboard", status_code=302)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=auth.COOKIE_TOKEN_MAX_AGE,
        expires=auth.COOKIE_TOKEN_MAX_AGE
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        max_age=auth.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
        expires=auth.REFRESH_TOKEN_EXPIRE_MINUTES * 60
    )

    return response


# =========================
# GET CURRENT USER
# =========================
def get_current_user(request: Request):
    access_token = request.cookies.get("access_token")

    if not access_token:
        return None

    user_id = auth.verify_token(access_token)

    if not user_id:
        return None

    with SessionLocal() as db:
        user = db.query(models.User).filter(
            models.User.id == user_id
        ).first()

    return user


# =========================
# DASHBOARD
# =========================
@router.get("/ui/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):

    user = get_current_user(request)

    if not user:
        return RedirectResponse("/ui/refresh")

    with SessionLocal() as db:
        expenses = db.query(models.Expense).filter(
            models.Expense.owner_id == user.id
        ).all()

    return templates.TemplateResponse(
    request=request,
    name="dashboard.html",
    context={
        "expenses": expenses,
        "user": user
    }
)


# =========================
# ADD EXPENSE PAGE
# =========================
@router.get("/ui/add-expense", response_class=HTMLResponse)
def add_page(request: Request):

    user = get_current_user(request)

    if not user:
        return RedirectResponse("/ui/refresh")

    return templates.TemplateResponse(
        request=request,
        name="add_expenses.html",
        context={}
    )

# =========================
# SAVE EXPENSE
# =========================
@router.post("/ui/add-expense")
def save_expense(
    request: Request,
    amount: float = Form(...),
    category: str = Form(...),
    description: str = Form(...),
    expense_date: str = Form(...)
):

    user = get_current_user(request)

    if not user:
        return RedirectResponse("/ui/refresh")

    with SessionLocal() as db:
        expense = models.Expense(
            amount=amount,
            category=category,
            description=description,
            expense_date=datetime.strptime(expense_date, "%Y-%m-%d").date(),
            owner_id=user.id
        )

        db.add(expense)
        db.commit()

    return RedirectResponse("/ui/dashboard", status_code=302)


# =========================
# DOWNLOAD PDF REPORT
# =========================
@router.get("/ui/download-pdf")
def download_pdf(request: Request):

    user = get_current_user(request)

    if not user:
        return RedirectResponse("/ui/refresh")

    with SessionLocal() as db:
        expenses = db.query(models.Expense).filter(
            models.Expense.owner_id == user.id
        ).all()

    file_path = generate_pdf(expenses)

    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename="expense_report.pdf"
    )


# =========================
# EMAIL PDF REPORT
# =========================
from fastapi.responses import HTMLResponse

@router.get("/ui/email-report")
async def email_report(request: Request):
    user = get_current_user(request)

    if not user:
        return RedirectResponse("/ui/refresh")

    with SessionLocal() as db:
        expenses = db.query(models.Expense).filter(
            models.Expense.owner_id == user.id
        ).all()

    file_path = generate_pdf(expenses)

    try:
        await send_email(
            user.email,
            f"<p>Hello {user.username},</p><p>Your expense report is attached.</p>",
            attachments=[file_path]
        )
        return HTMLResponse("Email sent successfully!")

    except Exception as e:
        return HTMLResponse(f"Email Error: {str(e)}")
# =========================
# LOGOUT
# =========================
@router.get("/ui/logout")
def logout():
    response = RedirectResponse("/ui/login")

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return response