import re
import time
from http import HTTPStatus
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, parse_qsl

from curl_cffi import requests
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
        self._session: requests.AsyncSession | None = None

    async def __aenter__(self):
        self._session = requests.AsyncSession()
        return self

    async def __aexit__(self, *exc):
        if self._session:
            await self._session.close()
            self._session = None

    @property
    def session(self) -> requests.AsyncSession:
        if self._session is None:
            raise RuntimeError("BoheSignClient must be used as async context manager")
        return self._session

    async def fetch_info(self, token: str) -> requests.Response:
        return await self.session.get(
            f"{self.BASE_URL}/api/user/info",
            headers={"Authorization": f"Bearer {token}"},
            impersonate=IMPERSONATE,
        )

    async def get_checkin_status(self, token: str) -> requests.Response:
        return await self.session.get(
            f"{self.BASE_URL}/api/sign/status",
            headers={"Authorization": f"Bearer {token}"},
            impersonate=IMPERSONATE,
        )

    async def sign(self, token: str) -> requests.Response:
        return await self.session.post(
            f"{self.BASE_URL}/api/sign/lottery",
            headers={"Authorization": f"Bearer {token}"},
            json={},
            impersonate=IMPERSONATE,
        )

    async def verify_token(self, token: str) -> tuple[bool, str]:
        r = await self.fetch_info(token)
        return r.status_code == HTTPStatus.OK and r.json().get("success"), r.text

    async def get_token(self, connect_token: str) -> str | None:
        t0 = time.perf_counter()
        r = await self.session.get(
            f"{self.BASE_URL}/api/auth/login", impersonate=IMPERSONATE
        )
        self.logger.debug(
            f"GET /api/auth/login -> {r.status_code} in {(time.perf_counter() - t0) * 1000:.0f}ms"
        )

        auth_url = r.json().get("auth_url")
        if not auth_url:
            raise ValueError("Failed to get auth_url")

        self.logger.debug(f"auth_url={redact_url(auth_url)}")

        ld_auth = LinuxDoConnect()
        ld_auth.set_connect_token(connect_token)

        try:
            t0 = time.perf_counter()
            approve_url = await ld_auth.approve_oauth(auth_url)
            self.logger.debug(
                f"OAuth approval completed in {(time.perf_counter() - t0) * 1000:.0f}ms"
            )
        except ValueError as e:
            status_match = re.search(r"status=(\d+)", str(e))
            if status_match and int(status_match.group(1)) == 429:
                raise RateLimitedError(
                    f"OAuth approval rate limited (429). auth_url={redact_url(auth_url)}"
                ) from e
            raise BoheAuthError(
                f"OAuth approval failed. auth_url={redact_url(auth_url)}"
            ) from e

        if not approve_url:
            raise ValueError(f"Failed to get approve_url. auth_url={redact_url(auth_url)}")

        r = await self.session.get(approve_url, impersonate=IMPERSONATE, allow_redirects=False)
        location = r.headers.get("Location")
        if not location:
            raise ValueError("Failed to extract token from redirect")

        token_values = parse_qs(urlparse(location).query).get("token")
        if not token_values:
            raise ValueError("Failed to extract token from redirect")

        return token_values[0]
