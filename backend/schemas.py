from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional


class EquipmentCreate(BaseModel):
    name: str
    type: str
    location: str
    status: str = "operational"
    last_maintenance_date: Optional[date] = None
    next_maintenance_due: date
    notes: Optional[str] = None


class EquipmentUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    last_maintenance_date: Optional[date] = None
    next_maintenance_due: Optional[date] = None
    notes: Optional[str] = None


class EquipmentResponse(BaseModel):
    id: str
    name: str
    type: str
    location: str
    status: str
    last_maintenance_date: Optional[date]
    next_maintenance_due: date
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class EquipmentOverdue(EquipmentResponse):
    days_overdue: int


class MaintenanceLogCreate(BaseModel):
    equipment_id: str
    performed_by: str
    maintenance_type: str
    description: str
    parts_replaced: Optional[str] = None
    performed_at: datetime
    next_due_date: date


class MaintenanceLogResponse(BaseModel):
    id: str
    equipment_id: str
    performed_by: str
    maintenance_type: str
    description: str
    parts_replaced: Optional[str]
    performed_at: datetime
    next_due_date: date
    created_at: datetime
    equipment_name: Optional[str] = None

    model_config = {"from_attributes": True}


class DashboardSummary(BaseModel):
    total_equipment: int
    operational_count: int
    overdue_count: int
    logs_this_month: int
