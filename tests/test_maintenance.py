import pytest
from datetime import date, datetime, timedelta


EQUIPMENT_PAYLOAD = {
    "name": "Pump Unit P-01",
    "type": "pump",
    "location": "Site B",
    "status": "operational",
    "last_maintenance_date": str(date.today() - timedelta(days=60)),
    "next_maintenance_due": str(date.today() + timedelta(days=30)),
}


@pytest.fixture
async def equipment_id(client):
    resp = await client.post("/equipment", json=EQUIPMENT_PAYLOAD)
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_maintenance_log(client):
    eq_resp = await client.post("/equipment", json=EQUIPMENT_PAYLOAD)
    eq_id = eq_resp.json()["id"]
    log_payload = {
        "equipment_id": eq_id,
        "performed_by": "Ahmed Al-Rashid",
        "maintenance_type": "routine",
        "description": "Full inspection and oil change",
        "parts_replaced": "Oil filter",
        "performed_at": datetime.now().isoformat(),
        "next_due_date": str(date.today() + timedelta(days=90)),
    }
    resp = await client.post("/maintenance", json=log_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["performed_by"] == "Ahmed Al-Rashid"
    assert data["equipment_name"] == EQUIPMENT_PAYLOAD["name"]


@pytest.mark.asyncio
async def test_list_maintenance_logs(client):
    resp = await client.get("/maintenance")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_filter_logs_by_equipment(client):
    eq_resp = await client.post("/equipment", json=EQUIPMENT_PAYLOAD)
    eq_id = eq_resp.json()["id"]
    log_payload = {
        "equipment_id": eq_id,
        "performed_by": "Test Tech",
        "maintenance_type": "corrective",
        "description": "Replaced valve",
        "performed_at": datetime.now().isoformat(),
        "next_due_date": str(date.today() + timedelta(days=60)),
    }
    await client.post("/maintenance", json=log_payload)
    resp = await client.get(f"/maintenance?equipment_id={eq_id}")
    assert resp.status_code == 200
    for log in resp.json():
        assert log["equipment_id"] == eq_id


@pytest.mark.asyncio
async def test_maintenance_log_updates_equipment(client):
    eq_resp = await client.post("/equipment", json=EQUIPMENT_PAYLOAD)
    eq_id = eq_resp.json()["id"]
    new_next_due = str(date.today() + timedelta(days=120))
    log_payload = {
        "equipment_id": eq_id,
        "performed_by": "Tech",
        "maintenance_type": "routine",
        "description": "Scheduled check",
        "performed_at": datetime.now().isoformat(),
        "next_due_date": new_next_due,
    }
    await client.post("/maintenance", json=log_payload)
    eq_resp = await client.get(f"/equipment/{eq_id}")
    assert eq_resp.json()["next_maintenance_due"] == new_next_due


@pytest.mark.asyncio
async def test_get_maintenance_log(client):
    eq_resp = await client.post("/equipment", json=EQUIPMENT_PAYLOAD)
    eq_id = eq_resp.json()["id"]
    log_payload = {
        "equipment_id": eq_id,
        "performed_by": "Tech B",
        "maintenance_type": "emergency",
        "description": "Emergency repair",
        "performed_at": datetime.now().isoformat(),
        "next_due_date": str(date.today() + timedelta(days=30)),
    }
    create_resp = await client.post("/maintenance", json=log_payload)
    log_id = create_resp.json()["id"]
    resp = await client.get(f"/maintenance/{log_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == log_id
