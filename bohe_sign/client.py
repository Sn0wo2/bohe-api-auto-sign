import re
import time
from http import HTTPStatus
from typing import Tuple
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, parse_qsl

from curl_cffi import requests, Response
from linux_do_connect import LinuxDoConnect, IMPERSONATE

from utils.logger import setup_logger

SENSITIVE_QUERY_PARAMS = frozenset({"state", "code", "access_token", "token"})


def redact_url(url: str) -> str:
    """Mask sensitive query parameters in URL for safe logging."""
    parsed = urlparse(url)
    safe_pairs = [
        (k, "***" if k.lower() in SENSITIVE_QUERY_PARAMS else v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
    ]
    return urlunparse(parsed._replace(query=urlencode(safe_pairs)))


class BoheAuthError(Exception):
    pass


class RateLimitedError(BoheAuthError):
    pass


class BoheSignClient:
    BASE_URL = "https://up.x666.me"

    def __init__(self):
        self.logger = setup_logger()

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
            t0 = time.perf_counter()
            r = await session.get(f"{self.BASE_URL}/api/auth/login", impersonate=IMPERSONATE)
            self.logger.debug(f"GET /api/auth/login -> {r.status_code} in {(time.perf_counter() - t0) * 1000:.0f}ms")

            data = r.json()
            auth_url = data.get("auth_url")
            if not auth_url:
                raise ValueError("Failed to get auth_url")

            self.logger.debug(f"auth_url={redact_url(auth_url)}")

            ld_auth = LinuxDoConnect()
            ld_auth.set_connect_token(connect_token)

            try:
                t0 = time.perf_counter()
                approve_url = await ld_auth.approve_oauth(auth_url)
                self.logger.debug(f"OAuth approval completed in {(time.perf_counter() - t0) * 1000:.0f}ms")
            except ValueError as e:
                if re.search(r"status=(\d+)", str(e)):
                    status_code = int(re.search(r"status=(\d+)", str(e)).group(1))
                    if status_code == 429:
                        raise RateLimitedError(
                            f"OAuth approval rate limited (429). "
                            f"auth_url={redact_url(auth_url)}"
                        ) from e
                raise BoheAuthError(
                    f"OAuth approval failed. auth_url={redact_url(auth_url)}"
                ) from e

            if not approve_url:
                raise ValueError(f"Failed to get approve_url. auth_url={redact_url(auth_url)}")

            r = await session.get(approve_url, impersonate=IMPERSONATE, allow_redirects=False)
            location = r.headers.get("Location")
            if not location:
                raise ValueError("Failed to extract token from redirect")

            tokens = parse_qs(urlparse(location).query).get("token")
            if not tokens:
                raise ValueError("Failed to extract token from redirect")

            return tokens[0]