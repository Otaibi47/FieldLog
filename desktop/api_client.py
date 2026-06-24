import asyncio
import httpx
import os
from config import API_BASE_URL

_token: str = ""


def _run(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


class APIClient:
    def __init__(self):
        self.base = API_BASE_URL
        self._token = ""

    def _headers(self):
        return {"Authorization": f"Bearer {self._token}"}

    def init_token(self):
        async def _fetch():
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.base}/token")
                resp.raise_for_status()
                return resp.json()["token"]
        self._token = _run(_fetch())

    # --- Equipment ---

    def get_equipment(self, status=None) -> list[dict]:
        async def _fetch():
            params = {"status": status} if status else {}
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.base}/equipment", headers=self._headers(), params=params)
                resp.raise_for_status()
                return resp.json()
        return _run(_fetch())

    def create_equipment(self, data: dict) -> dict:
        async def _fetch():
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(f"{self.base}/equipment", headers=self._headers(), json=data)
                resp.raise_for_status()
                return resp.json()
        return _run(_fetch())

    def update_equipment(self, item_id: str, data: dict) -> dict:
        async def _fetch():
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.put(f"{self.base}/equipment/{item_id}", headers=self._headers(), json=data)
                resp.raise_for_status()
                return resp.json()
        return _run(_fetch())

    def delete_equipment(self, item_id: str):
        async def _fetch():
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.delete(f"{self.base}/equipment/{item_id}", headers=self._headers())
                resp.raise_for_status()
        _run(_fetch())

    def get_overdue(self) -> list[dict]:
        async def _fetch():
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.base}/equipment/alerts/overdue", headers=self._headers())
                resp.raise_for_status()
                return resp.json()
        return _run(_fetch())

    # --- Maintenance ---

    def get_maintenance_logs(self, equipment_id=None) -> list[dict]:
        async def _fetch():
            params = {"equipment_id": equipment_id} if equipment_id else {}
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.base}/maintenance", headers=self._headers(), params=params)
                resp.raise_for_status()
                return resp.json()
        return _run(_fetch())

    def create_maintenance_log(self, data: dict) -> dict:
        async def _fetch():
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(f"{self.base}/maintenance", headers=self._headers(), json=data)
                resp.raise_for_status()
                return resp.json()
        return _run(_fetch())

    # --- Dashboard ---

    def get_dashboard_summary(self) -> dict:
        async def _fetch():
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.base}/dashboard/summary", headers=self._headers())
                resp.raise_for_status()
                return resp.json()
        return _run(_fetch())
