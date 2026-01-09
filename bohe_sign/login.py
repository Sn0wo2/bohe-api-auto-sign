import traceback
from http import HTTPStatus
from urllib.parse import urlparse, parse_qs
from curl_cffi import requests, Response
from store.token import load_tokens, save_tokens
from linux_do_connect import LinuxDoConnect

IMPERSONATE = "chrome"

async def verify_bohe_token(token: str) -> bool:
    if not token:
        return False
    
    url = "https://up.x666.me/api/user/info"
    
    try:
        async with requests.AsyncSession() as session:
            r = await session.post(url, headers={
                "Authorization": f"Bearer {token}"
            }, json={}, impersonate=IMPERSONATE)
            if r.status_code == HTTPStatus.OK:
                return r.json().get("success") == True
            return False
    except Exception:
        return False

async def fetch_token_workflow(token: str | None = None, connect_token: str | None = None) -> tuple[str | None, str | None, str | None]:
    try:
        async with requests.AsyncSession() as session:
            # 薄荷的恩情还不完 ✋😭✋
            r: Response = await session.get("https://up.x666.me/api/auth/login", impersonate=IMPERSONATE)
            auth_url = r.json().get("authUrl")
            
            if not auth_url:
                print("Failed to get authUrl")
                return None, connect_token, token

            ld_auth = LinuxDoConnect()

            if token is not None and connect_token is None:
                connect_token, token = await (await ld_auth.login(token)).get_connect_token()

            ld_auth.session.cookies.set("auth.session-token", connect_token, domain="connect.linux.do")

            approve_url = await ld_auth.approve_oauth(auth_url)
            if not approve_url:
                return None, connect_token, token
            
            r: Response = await session.get(approve_url,
                                            impersonate=IMPERSONATE,
                                            allow_redirects=False)
            location = r.headers.get("Location")
            if location:
                token_list = parse_qs(urlparse(location).query).get("token")
                if token_list:
                    return token_list[0], connect_token, token
                    
    except Exception as e:
        print(f"Token acquisition failed: {e}")
        traceback.print_exc()

    return None, connect_token, token

async def get_bohe_token(token: str = "") -> tuple[str | None, str | None, str | None]:
    tokens = load_tokens()
    bohe_token = tokens.get("bohe_sign_token")
    linux_do_connect_token = tokens.get("linux_do_connect_token")
    linux_do_token = tokens.get("linux_do_token")

    if bohe_token and await verify_bohe_token(bohe_token):
        print("Using stored valid bohe_sign_token")
        return bohe_token, linux_do_connect_token, linux_do_token
    
    print("bohe_sign_token invalid!")

    if linux_do_connect_token:
        print("Attempting to refresh bohe_sign_token using stored linux_do_connect_token...")
        new_bohe, new_ld_connect, new_ld = await fetch_token_workflow(connect_token=linux_do_connect_token)
        if new_bohe:
            print("Refreshed bohe_sign_token successfully via stored linux_do_connect_token")
            save_tokens(new_bohe, new_ld_connect, new_ld)
            return new_bohe, new_ld_connect or linux_do_connect_token, new_ld or linux_do_token
        print("Refresh bohe_sign_token via linux_do_connect_token failed")
    
    target_cookie = token if token else linux_do_token
    
    if target_cookie:
        print("Attempting full login with linux_do_token/cookie...")
        new_bohe, new_ld_connect, new_ld = await fetch_token_workflow(token=target_cookie)
        
        if new_bohe:
            print("Login successful")
            save_tokens(new_bohe, new_ld_connect, new_ld)
            return new_bohe, new_ld_connect, new_ld
    else:
        print("No LINUX_DO_TOKEN available for full login.")
        
    return None, linux_do_connect_token, linux_do_token