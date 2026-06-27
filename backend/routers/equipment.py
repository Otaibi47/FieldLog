import html as _html
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import Equipment, MaintenanceLog
from schemas import EquipmentCreate, EquipmentUpdate, EquipmentResponse, EquipmentOverdue
from auth import verify_token
from audit_service import log_action

router = APIRouter(prefix="/equipment", tags=["equipment"])


# ── CRUD ─────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[EquipmentResponse])
async def list_equipment(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_token),
):
    query = select(Equipment).order_by(Equipment.name)
    if status:
        query = query.where(Equipment.status == status)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=EquipmentResponse, status_code=201)
async def create_equipment(
    body: EquipmentCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_token),
):
    item = Equipment(**body.model_dump())
    db.add(item)
    await log_action(db, "created", "equipment", item.id, item.name,
                     f"Equipment '{item.name}' was created")
    await db.commit()
    await db.refresh(item)
    return item


@router.get("/alerts/overdue", response_model=list[EquipmentOverdue])
async def list_overdue(db: AsyncSession = Depends(get_db), _=Depends(verify_token)):
    today = date.today()
    result = await db.execute(
        select(Equipment)
        .where(Equipment.next_maintenance_due < today)
        .order_by(Equipment.next_maintenance_due)
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
async def get_equipment(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_token),
):
    item = await db.get(Equipment, item_id)
    if not item:
        raise HTTPException(404, "Equipment not found")
    return item


@router.put("/{item_id}", response_model=EquipmentResponse)
async def update_equipment(
    item_id: str,
    body: EquipmentUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_token),
):
    item = await db.get(Equipment, item_id)
    if not item:
        raise HTTPException(404, "Equipment not found")

    old_status = item.status
    updated_fields = body.model_dump(exclude_unset=True)
    for field, value in updated_fields.items():
        setattr(item, field, value)

    if "status" in updated_fields and item.status != old_status:
        description = (
            f"Equipment '{item.name}' status changed "
            f"from '{old_status}' to '{item.status}'"
        )
        action_type = "status_changed"
    else:
        description = f"Equipment '{item.name}' was updated"
        action_type = "updated"

    await log_action(db, action_type, "equipment", item.id, item.name, description)
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_equipment(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_token),
):
    item = await db.get(Equipment, item_id)
    if not item:
        raise HTTPException(404, "Equipment not found")
    name = item.name
    await log_action(db, "deleted", "equipment", item_id, name,
                     f"Equipment '{name}' was permanently deleted")
    await db.delete(item)
    await db.commit()


# ── Public maintenance history page (scanned via QR code) ────────────────────

@router.get("/{item_id}/history", response_class=HTMLResponse, include_in_schema=False)
async def equipment_history(item_id: str, db: AsyncSession = Depends(get_db)):
    item = await db.get(Equipment, item_id)
    if not item:
        return HTMLResponse("<h1>Equipment not found</h1>", status_code=404)

    result = await db.execute(
        select(MaintenanceLog)
        .where(MaintenanceLog.equipment_id == item_id)
        .order_by(MaintenanceLog.performed_at.desc())
    )
    logs = result.scalars().all()

    return HTMLResponse(_history_html(item, logs))


def _e(v):
    return _html.escape(str(v) if v is not None else "")


def _history_html(item: Equipment, logs: list) -> str:
    status_class = {
        "operational": "status-operational",
        "degraded":    "status-degraded",
        "offline":     "status-offline",
    }.get(item.status, "status-offline")

    logs_html = ""
    if logs:
        for log in logs:
            parts_html = (
                f'<div class="log-parts">Parts replaced: {_e(log.parts_replaced)}</div>'
                if log.parts_replaced else ""
            )
            performed_str = (
                log.performed_at.strftime("%b %d, %Y  %I:%M %p")
                if log.performed_at else "—"
            )
            logs_html += f"""
<div class="log-card">
  <div class="log-top">
    <span class="log-type">{_e(log.maintenance_type.title())}</span>
    <span class="log-date">{_e(performed_str)}</span>
  </div>
  <div class="log-by">By {_e(log.performed_by)}</div>
  <div class="log-desc">{_e(log.description)}</div>
  {parts_html}
  <div class="next-due">
    <span class="ndue-lbl">Next due: </span>
    <span class="ndue-val">{_e(str(log.next_due_date))}</span>
  </div>
</div>"""
    else:
        logs_html = '<div class="empty">No maintenance records on file.</div>'

    generated = datetime.utcnow().strftime("%b %d, %Y  %I:%M %p UTC")
    count = len(logs)
    plural = "s" if count != 1 else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_e(item.name)} — FieldLog</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
      background:#0F172A;color:#F1F5F9;min-height:100vh}}
.header{{background:#1E293B;border-bottom:3px solid #3B82F6;padding:20px 16px}}
.brand{{color:#3B82F6;font-size:11px;font-weight:700;letter-spacing:1.5px;
        text-transform:uppercase;margin-bottom:8px}}
h1{{font-size:22px;font-weight:700;margin-bottom:10px;line-height:1.2}}
.meta{{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}}
.badge{{padding:4px 11px;border-radius:12px;font-size:12px;font-weight:500}}
.bt{{background:#1E3A5F;color:#93C5FD}}
.bl{{background:#1E293B;color:#94A3B8;border:1px solid #334155}}
.status-operational{{background:#14532D;color:#4ADE80}}
.status-degraded{{background:#451A03;color:#FBBF24}}
.status-offline{{background:#1C0B0B;color:#F87171}}
.section{{padding:16px}}
.section-title{{font-size:12px;font-weight:700;color:#94A3B8;
                text-transform:uppercase;letter-spacing:.5px;margin-bottom:12px}}
.log-card{{background:#1E293B;border-radius:8px;padding:14px 16px;
           margin-bottom:10px;border-left:3px solid #3B82F6}}
.log-top{{display:flex;justify-content:space-between;align-items:flex-start;
          gap:8px;margin-bottom:6px}}
.log-type{{font-weight:600;font-size:14px}}
.log-date{{font-size:11px;color:#94A3B8;white-space:nowrap}}
.log-by{{font-size:12px;color:#60A5FA;margin-bottom:6px}}
.log-desc{{font-size:13px;color:#CBD5E1;line-height:1.5}}
.log-parts{{font-size:12px;color:#94A3B8;margin-top:6px}}
.next-due{{display:inline-block;background:#172554;border-radius:6px;
           padding:5px 10px;margin-top:8px;font-size:12px}}
.ndue-lbl{{color:#94A3B8}}.ndue-val{{color:#93C5FD;font-weight:600}}
.empty{{text-align:center;padding:40px 20px;color:#94A3B8;font-size:14px}}
.footer{{text-align:center;padding:20px;color:#475569;font-size:11px;
         border-top:1px solid #1E293B;margin-top:8px}}
</style>
</head>
<body>
<div class="header">
  <div class="brand">FieldLog &mdash; Maintenance Record</div>
  <h1>{_e(item.name)}</h1>
  <div class="meta">
    <span class="badge bt">{_e(item.type.title())}</span>
    <span class="badge bl">{_e(item.location)}</span>
    <span class="badge {status_class}">{_e(item.status.title())}</span>
  </div>
</div>
<div class="section">
  <div class="section-title">{count} Maintenance Record{plural}</div>
  {logs_html}
</div>
<div class="footer">Generated by FieldLog &mdash; {_e(generated)}</div>
</body>
</html>"""
