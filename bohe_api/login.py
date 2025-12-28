from http import HTTPStatus

from curl_cffi import AsyncSession
from curl_cffi import Response
from linux_do_connect import IMPERSONATE
from linux_do_oauth import LinuxDoOAuth, SESSION_KEY


async def fetch_self(session: AsyncSession) -> Response:
    if not session or not session.cookies.get(SESSION_KEY, domain="x666.me"):
        raise ValueError("Session is empty or missing session cookie")
    return await session.get("https://x666.me/api/user/self", impersonate=IMPERSONATE)

async def verify_bohe_api_token(session: AsyncSession) -> tuple[bool, str]:
    r: Response = await fetch_self(session)
    if r.status_code == HTTPStatus.OK:
        is_success = r.json().get("success") == True
        return is_success, r.text
    return False, f"HTTP {r.status_code}: {r.text}"

async def get_api_session(connect_token) -> AsyncSession:
    oauth = LinuxDoOAuth(base_url="https://x666.me")
    r: Response = await (await oauth.fetch_client_id()).login(connect_token=connect_token)

    session = await oauth.get_session()
    json_data = r.json()
    if json_data.get("success") and "data" in json_data:
        session.headers["new-api-user"] = str(json_data.get("data").get("id"))

    return session
