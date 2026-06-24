from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from database import get_db
from models import Equipment
from schemas import EquipmentCreate, EquipmentUpdate, EquipmentResponse, EquipmentOverdue
from auth import verify_token

router = APIRouter(prefix="/equipment", tags=["equipment"])


@router.get("", response_model=list[EquipmentResponse])
async def list_equipment(status: str | None = None, db: AsyncSession = Depends(get_db), _=Depends(verify_token)):
    query = select(Equipment).order_by(Equipment.name)
    if status:
        query = query.where(Equipment.status == status)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=EquipmentResponse, status_code=201)
async def create_equipment(body: EquipmentCreate, db: AsyncSession = Depends(get_db), _=Depends(verify_token)):
    item = Equipment(**body.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.get("/alerts/overdue", response_model=list[EquipmentOverdue])
async def list_overdue(db: AsyncSession = Depends(get_db), _=Depends(verify_token)):
    today = date.today()
    result = await db.execute(
        select(Equipment).where(Equipment.next_maintenance_due < today).order_by(Equipment.next_maintenance_due)
    )
    items = result.scalars().all()
    return [
        EquipmentOverdue(
            **{c.name: getattr(item, c.name) for c in item.__table__.columns},
            days_overdue=(today - item.next_maintenance_due).days,
        )
        for item in items
    ]


@router.get("/{item_id}", response_model=EquipmentResponse)
async def get_equipment(item_id: str, db: AsyncSession = Depends(get_db), _=Depends(verify_token)):
    item = await db.get(Equipment, item_id)
    if not item:
        raise HTTPException(404, "Equipment not found")
    return item


@router.put("/{item_id}", response_model=EquipmentResponse)
async def update_equipment(item_id: str, body: EquipmentUpdate, db: AsyncSession = Depends(get_db), _=Depends(verify_token)):
    item = await db.get(Equipment, item_id)
    if not item:
        raise HTTPException(404, "Equipment not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_equipment(item_id: str, db: AsyncSession = Depends(get_db), _=Depends(verify_token)):
    item = await db.get(Equipment, item_id)
    if not item:
        raise HTTPException(404, "Equipment not found")
    await db.delete(item)
    await db.commit()
