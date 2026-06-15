from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from .database import Base, engine

# import routers from this package
from . import users, expenses, reports
from ui.ui import router as ui_router

app = FastAPI(title="Expense Tracker")

Base.metadata.create_all(bind=engine)

# register routers
app.include_router(users.router)
app.include_router(expenses.router)
app.include_router(reports.router)
app.include_router(ui_router)

# templates + static (optional)
try:
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    templates = Jinja2Templates(directory="app/templates")
except Exception:
    templates = None


@app.get("/")
def root():
    return RedirectResponse(url="/ui/login")