import pytest
from datetime import date, timedelta


EQUIPMENT_PAYLOAD = {
    "name": "Compressor Unit C-04",
    "type": "compressor",
    "location": "Block 7 - North Field",
    "status": "operational",
    "last_maintenance_date": str(date.today() - timedelta(days=30)),
    "next_maintenance_due": str(date.today() + timedelta(days=60)),
    "notes": "Runs well",
}


@pytest.mark.asyncio
async def test_create_equipment(client):
    resp = await client.post("/equipment", json=EQUIPMENT_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == EQUIPMENT_PAYLOAD["name"]
    assert "id" in data


@pytest.mark.asyncio
async def test_list_equipment(client):
    resp = await client.get("/equipment")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_get_equipment(client):
    create_resp = await client.post("/equipment", json=EQUIPMENT_PAYLOAD)
    item_id = create_resp.json()["id"]
    resp = await client.get(f"/equipment/{item_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == item_id


@pytest.mark.asyncio
async def test_update_equipment(client):
    create_resp = await client.post("/equipment", json=EQUIPMENT_PAYLOAD)
    item_id = create_resp.json()["id"]
    resp = await client.put(f"/equipment/{item_id}", json={"status": "degraded"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "degraded"


@pytest.mark.asyncio
async def test_delete_equipment(client):
    create_resp = await client.post("/equipment", json=EQUIPMENT_PAYLOAD)
    item_id = create_resp.json()["id"]
    resp = await client.delete(f"/equipment/{item_id}")
    assert resp.status_code == 204
    get_resp = await client.get(f"/equipment/{item_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_overdue_equipment(client):
    overdue_payload = {**EQUIPMENT_PAYLOAD, "next_maintenance_due": str(date.today() - timedelta(days=5))}
    await client.post("/equipment", json=overdue_payload)
    resp = await client.get("/equipment/alerts/overdue")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 1
    assert items[0]["days_overdue"] >= 5


@pytest.mark.asyncio
async def test_filter_by_status(client):
    await client.post("/equipment", json={**EQUIPMENT_PAYLOAD, "status": "offline"})
    resp = await client.get("/equipment?status=offline")
    assert resp.status_code == 200
    for item in resp.json():
        assert item["status"] == "offline"
