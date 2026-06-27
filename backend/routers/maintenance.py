from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import MaintenanceLog, Equipment
from schemas import MaintenanceLogCreate, MaintenanceLogResponse
from auth import verify_token
from audit_service import log_action

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@router.get("", response_model=list[MaintenanceLogResponse])
async def list_logs(
    equipment_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_token),
):
    query = select(MaintenanceLog).order_by(MaintenanceLog.performed_at.desc())
    if equipment_id:
        query = query.where(MaintenanceLog.equipment_id == equipment_id)
    result = await db.execute(query)
    logs = result.scalars().all()
    out = []
    for log in logs:
        equipment = await db.get(Equipment, log.equipment_id)
        data = MaintenanceLogResponse.model_validate(log)
        data.equipment_name = equipment.name if equipment else None
        out.append(data)
    return out


@router.post("", response_model=MaintenanceLogResponse, status_code=201)
async def create_log(
    body: MaintenanceLogCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_token),
):
    equipment = await db.get(Equipment, body.equipment_id)
    if not equipment:
        raise HTTPException(404, "Equipment not found")

    log = MaintenanceLog(**body.model_dump())
    db.add(log)

    equipment.last_maintenance_date = body.performed_at.date()
    equipment.next_maintenance_due = body.next_due_date

    await log_action(
        db, "created", "maintenance_log", log.id, equipment.name,
        f"Maintenance log added for '{equipment.name}' — "
        f"{body.maintenance_type.title()} by {body.performed_by}",
    )

    await db.commit()
    await db.refresh(log)

    data = MaintenanceLogResponse.model_validate(log)
    data.equipment_name = equipment.name
    return data


@router.get("/{log_id}", response_model=MaintenanceLogResponse)
async def get_log(
    log_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_token),
):
    log = await db.get(MaintenanceLog, log_id)
    if not log:
        raise HTTPException(404, "Maintenance log not found")
    equipment = await db.get(Equipment, log.equipment_id)
    data = MaintenanceLogResponse.model_validate(log)
    data.equipment_name = equipment.name if equipment else None
    return data
