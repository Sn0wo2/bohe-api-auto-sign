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
        self.logger.info("Refreshing connect token...")
        return await (await LinuxDoConnect(token=ld_token).login()).get_connect_token()

    async def get_valid_token(self) -> Optional[str]:
        tokens = load_tokens()
        sign_token = tokens.get("bohe_sign_token")
        connect_token = tokens.get("linux_do_connect_token")
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