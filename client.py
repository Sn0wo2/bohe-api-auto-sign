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
                connect_token, _ = await connect.get_connect_token()
                self.logger.info("Successfully obtained connect token from linux.do")
                return connect_token, ld_token
            except Exception as e:
                self.logger.error(f"Failed to extract connect token: {str(e)}")
                raise e
        except Exception as e:
            self.logger.error(f"LinuxDo login flow failed: {str(e)}")
            raise


    async def get_valid_token(self) -> Optional[str]:
        tokens = load_tokens()
        sign_token = tokens.get("bohe_sign_token") or os.getenv("BOHE_SIGN_TOKEN")
        connect_token = tokens.get("linux_do_connect_token") or os.getenv("LINUX_DO_CONNECT_TOKEN")
        ld_token = tokens.get("linux_do_token") or os.getenv("LINUX_DO_TOKEN")


        # 1. Verify existing token
        if sign_token:
            self.logger.info("Verifying existing Bohe sign token...")
            valid, _ = await self.sign_client.verify_token(sign_token)
            if valid:
                self.logger.info("Existing Bohe sign token is still valid")
                return sign_token
            self.logger.warning("Stored Bohe sign token is invalid/expired, attempting to refresh...")


        # 2. Login flow with retry & fallback
        for attempt in range(1, 4):
            try:
                if attempt > 1:
                    self.logger.info(f"Retrying token refresh (attempt {attempt}/3)...")
                
                # 如果没有 connect_token 或者是在重试中，尝试刷新它
                if not connect_token or attempt > 1:
                    connect_token, ld_token = await self._get_connect_token(ld_token)

                new_token = await self.sign_client.get_token(connect_token)
                
                save_tokens(bohe_sign_token=new_token, 
                            linux_do_connect_token=connect_token, 
                            linux_do_token=ld_token)
                self.logger.info("Successfully obtained and saved new token")
                return new_token
            except Exception as e:
                self.logger.warning(f"Token refresh attempt {attempt} failed: {e}")
                if attempt == 3:
                    self.logger.error("All 3 attempts to refresh token failed.")
                    raise
                import asyncio
                await asyncio.sleep(attempt * 2)
        return None


    async def sign(self, token: str) -> bool:
        try:
            # Check status
            self.logger.info("Checking check-in status...")
            status_r = await self.sign_client.get_checkin_status(token)
            if status_r.status_code == HTTPStatus.OK:
                status_data = status_r.json()
                if not status_data.get("can_spin"):
                    self.logger.info("Already checked in today (confirmed by server)")
                    return True
                self.logger.info("Ready to sign in, performing spin...")
            
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