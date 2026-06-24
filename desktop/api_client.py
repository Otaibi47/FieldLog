import asyncio
import httpx
from config import API_BASE_URL


class APIClient:
    def __init__(self):
        self.base = API_BASE_URL
        self._token = ""

    def _headers(self):
        return {"Authorization": f"Bearer {self._token}"}

    def _run(self, coro):
        return asyncio.run(coro)

    def init_token(self):
        async def _fetch():
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(f"{self.base}/token")
                r.raise_for_status()
                return r.json()["token"]
        try:
            self._token = self._run(_fetch())
        except Exception:
            pass

    def get_equipment(self, status=None) -> list[dict]:
        async def _fetch():
            params = {"status": status} if status else {}
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get(f"{self.base}/equipment", headers=self._headers(), params=params)
                r.raise_for_status()
                return r.json()
        return self._run(_fetch())

    def create_equipment(self, data: dict) -> dict:
        async def _fetch():
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.post(f"{self.base}/equipment", headers=self._headers(), json=data)
                r.raise_for_status()
                return r.json()
        return self._run(_fetch())

    def update_equipment(self, item_id: str, data: dict) -> dict:
        async def _fetch():
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.put(f"{self.base}/equipment/{item_id}", headers=self._headers(), json=data)
                r.raise_for_status()
                return r.json()
        return self._run(_fetch())

    def delete_equipment(self, item_id: str):
        async def _fetch():
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.delete(f"{self.base}/equipment/{item_id}", headers=self._headers())
                r.raise_for_status()
        self._run(_fetch())

    def get_overdue(self) -> list[dict]:
        async def _fetch():
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get(f"{self.base}/equipment/alerts/overdue", headers=self._headers())
                r.raise_for_status()
                return r.json()
        return self._run(_fetch())

    def get_maintenance_logs(self, equipment_id=None) -> list[dict]:
        async def _fetch():
            params = {"equipment_id": equipment_id} if equipment_id else {}
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get(f"{self.base}/maintenance", headers=self._headers(), params=params)
                r.raise_for_status()
                return r.json()
        return self._run(_fetch())

    def create_maintenance_log(self, data: dict) -> dict:
        async def _fetch():
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.post(f"{self.base}/maintenance", headers=self._headers(), json=data)
                r.raise_for_status()
                return r.json()
        return self._run(_fetch())

    def get_dashboard_summary(self) -> dict:
        async def _fetch():
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get(f"{self.base}/dashboard/summary", headers=self._headers())
                r.raise_for_status()
                return r.json()
        return self._run(_fetch())
