import os
from http import HTTPStatus
from typing import Optional

from curl_cffi.requests import Response
from linux_do_connect import LinuxDoConnect

from bohe_sign.client import BoheSignClient
from store.token import load_tokens, save_tokens
from utils.logger import setup_logger


class BoheClient:
    def __init__(self):
        self.logger = setup_logger()
        self.sign_client = BoheSignClient()

    async def _get_connect_token(self, ld_token: Optional[str]) -> tuple[str, Optional[str]]:
        if not ld_token:
            raise ValueError("LINUX_DO_TOKEN is required to refresh connect token")
        self.logger.info(f"Refreshing connect token with linux_do_token (ending in ...{ld_token[-5:] if ld_token else 'None'})")
        try:
            connect = LinuxDoConnect(token=ld_token)
            await connect.login()
            self.logger.info("Successfully logged in to linux.do")
            
            try:
                return await connect.get_connect_token()
            except Exception as e:
                print(f"\n[!!! DIAGNOSTIC START !!!]")
                print(f"Error Type: {type(e).__name__}")
                print(f"Error Message: {str(e)}")
                
                # 寻找内部 session
                session = None
                for attr in ['client', 'session', '_client', '_session']:
                    if hasattr(connect, attr):
                        session = getattr(connect, attr)
                        print(f"Found session in attribute: {attr}")
                        break
                
                if session:
                    try:
                        # 强行请求首页并抓取信息
                        resp = await session.get("https://connect.linux.do/", allow_redirects=True)
                        print(f"Diagnostic URL: {resp.url}")
                        print(f"Diagnostic Status: {resp.status_code}")
                        print(f"Diagnostic Body Snippet: {resp.text[:1000]}")
                    except Exception as diag_e:
                        print(f"Diagnostic Request Failed: {diag_e}")
                
                print(f"[!!! DIAGNOSTIC END !!!]\n")
                raise e
        except Exception as e:
            self.logger.error(f"LinuxDoConnect error: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            raise


    async def get_valid_token(self) -> Optional[str]:
        tokens = load_tokens()
        sign_token = tokens.get("bohe_sign_token") or os.getenv("BOHE_SIGN_TOKEN")
        connect_token = tokens.get("linux_do_connect_token") or os.getenv("LINUX_DO_CONNECT_TOKEN")
        ld_token = tokens.get("linux_do_token") or os.getenv("LINUX_DO_TOKEN")


        # 1. Verify existing token
        if sign_token:
            valid, _ = await self.sign_client.verify_token(sign_token)
            if valid:
                return sign_token
            self.logger.warning("Stored token is invalid, attempting to refresh...")

        # 2. Login flow
        try:
            if not connect_token:
                connect_token, ld_token = await self._get_connect_token(ld_token)

            try:
                new_token = await self.sign_client.get_token(connect_token)
            except Exception:
                # Retry once with refreshed connect token
                self.logger.info("Connect token might be expired, refreshing...")
                connect_token, ld_token = await self._get_connect_token(ld_token)
                new_token = await self.sign_client.get_token(connect_token)

            save_tokens(bohe_sign_token=new_token, 
                        linux_do_connect_token=connect_token, 
                        linux_do_token=ld_token)
            self.logger.info("Successfully obtained and saved new token")
            return new_token
        except Exception as e:
            self.logger.error(f"Failed to refresh token: {e}")
            return None

    async def sign(self, token: str) -> bool:
        try:
            # Check status
            status_r = await self.sign_client.get_checkin_status(token)
            if status_r.status_code == HTTPStatus.OK and not status_r.json().get("can_spin"):
                self.logger.info("Already checked in today")
                return True
            
            # Perform spin
            r = await self.sign_client.sign(token)
            if r.status_code == HTTPStatus.OK:
                data = r.json()
                if data.get("success"):
                    self.logger.info(f"Sign successful: {data.get('label')} (+{data.get('quota')} quota)")
                    return True
                self.logger.warning(f"Sign failed: {data.get('message')}")
            else:
                self.logger.error(f"Sign error: {r.status_code}")
        except Exception as e:
            self.logger.error(f"Sign exception: {e}")
        return False