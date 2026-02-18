from http import HTTPStatus
from urllib.parse import urlparse, parse_qs
from typing import Tuple, Optional, Any

from curl_cffi import requests, Response
from linux_do_connect import LinuxDoConnect, IMPERSONATE


class BoheSignClient:
    BASE_URL = "https://up.x666.me"

    async def fetch_info(self, token: str) -> Response:
        async with requests.AsyncSession() as session:
            return await session.get(f"{self.BASE_URL}/api/user/info",
                                   headers={"Authorization": f"Bearer {token}"},
                                   impersonate=IMPERSONATE)

    async def get_checkin_status(self, token: str) -> Response:
        async with requests.AsyncSession() as session:
            return await session.get(f"{self.BASE_URL}/api/checkin/status",
                                   headers={"Authorization": f"Bearer {token}"},
                                   impersonate=IMPERSONATE)

    async def sign(self, token: str) -> Response:
        async with requests.AsyncSession() as session:
            return await session.post(f"{self.BASE_URL}/api/checkin/spin",
                                    headers={"Authorization": f"Bearer {token}"},
                                    json={}, impersonate=IMPERSONATE)

    async def verify_token(self, token: str) -> Tuple[bool, str]:
        r = await self.fetch_info(token)
        return r.status_code == HTTPStatus.OK and r.json().get("success"), r.text

    async def get_token(self, connect_token: str) -> str:
        async with requests.AsyncSession() as session:
            # 薄荷的恩情还不完 ✋😭✋
            r = await session.get(f"{self.BASE_URL}/api/auth/login", impersonate=IMPERSONATE)
            auth_url = r.json().get("auth_url")
            if not auth_url:
                raise ValueError("Failed to get auth_url")

            ld_auth = LinuxDoConnect()
            ld_auth.set_connect_token(connect_token)

            approve_url = await ld_auth.approve_oauth(auth_url)
            if not approve_url:
                raise ValueError("Failed to get approve_url")

            r = await session.get(approve_url, impersonate=IMPERSONATE, allow_redirects=False)
            location = r.headers.get("Location")
            if location:
                tokens = parse_qs(urlparse(location).query).get("token")
                if tokens:
                    return tokens[0]

            raise ValueError("Failed to extract token from redirect")