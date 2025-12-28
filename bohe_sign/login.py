from http import HTTPStatus
from urllib.parse import urlparse, parse_qs

from curl_cffi import requests, Response
from linux_do_connect import LinuxDoConnect, IMPERSONATE

FIRST_INFO = None


async def fetch_info(token: str) -> Response:
    if not token or token.strip() == "":
        raise ValueError("Token is empty")
    async with requests.AsyncSession() as session:
        return await session.post("https://qd.x666.me/api/user/info", headers={
            "Authorization": f"Bearer {token}"
        }, json={}, impersonate=IMPERSONATE)


async def verify_bohe_token(token: str) -> tuple[bool, str]:
    r: Response = await fetch_info(token)
    FIRST_INFO = r
    if r.status_code == HTTPStatus.OK:
        return r.json().get("success") == True, r.text
    return False, f"HTTP {r.status_code}: {r.text}"


async def get_sign_token(connect_token: str) -> str:
    async with requests.AsyncSession() as session:
        # 薄荷的恩情还不完 ✋😭✋
        r: Response = await session.get("https://qd.x666.me/api/auth/login", impersonate=IMPERSONATE)
        auth_url = r.json().get("authUrl")

        if not auth_url:
            raise ValueError("Failed to get authUrl from Bohe API")

        ld_auth = LinuxDoConnect()
        ld_auth.set_connect_token(connect_token)

        approve_url = await ld_auth.approve_oauth(auth_url)
        if not approve_url:
            raise ValueError("Failed to get approve_url from LinuxDoConnect")

        r: Response = await session.get(approve_url,
                                        impersonate=IMPERSONATE,
                                        allow_redirects=False)
        location = r.headers.get("Location")
        if location:
            token_list = parse_qs(urlparse(location).query).get("token")
            if token_list:
                return token_list[0]

        raise ValueError("Failed to extract token from redirect location")
