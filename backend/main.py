import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, func
from datetime import date, datetime

from database import init_db, AsyncSessionLocal
from routers import equipment, maintenance
from alert_service import run_alert_check
from auth import create_token, verify_token
from schemas import DashboardSummary
from models import Equipment, MaintenanceLog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def scheduled_alert_check():
    async with AsyncSessionLocal() as db:
        await run_alert_check(db)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    scheduler.add_job(scheduled_alert_check, "interval", hours=24, id="alert_check")
    scheduler.start()
    logger.info("FieldLog backend started")
    yield
    scheduler.shutdown()


app = FastAPI(title="FieldLog API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(equipment.router)
app.include_router(maintenance.router)


@app.get("/token")
async def get_token():
    return {"token": create_token()}


@app.get("/dashboard/summary", response_model=DashboardSummary, tags=["dashboard"])
async def dashboard_summary(_=Depends(verify_token)):
    async with AsyncSessionLocal() as db:
        total = (await db.execute(select(func.count()).select_from(Equipment))).scalar()
        operational = (
            await db.execute(
                select(func.count()).select_from(Equipment).where(Equipment.status == "operational")
            )
        ).scalar()
        today = date.today()
        overdue = (
            await db.execute(
                select(func.count()).select_from(Equipment).where(Equipment.next_maintenance_due < today)
            )
        ).scalar()
        logs_month = (
            await db.execute(
                select(func.count())
                .select_from(MaintenanceLog)
                .where(MaintenanceLog.performed_at >= datetime(today.year, today.month, 1))
            )
        ).scalar()
    return DashboardSummary(
        total_equipment=total,
        operational_count=operational,
        overdue_count=overdue,
        logs_this_month=logs_month,
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
