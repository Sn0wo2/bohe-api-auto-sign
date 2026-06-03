import asyncio
import os
import random
import time
from http import HTTPStatus
from typing import Optional

from curl_cffi.requests import Response
from linux_do_connect import LinuxDoConnect

from bohe_sign.client import BoheSignClient, RateLimitedError
from store.token import load_tokens, save_tokens
from utils.logger import setup_logger


class BoheClient:
    def __init__(self):
        self.logger = setup_logger()
        self.sign_client = BoheSignClient()

    async def _get_connect_token(self, ld_token: Optional[str]) -> tuple[str, Optional[str]]:
        if not ld_token:
            raise ValueError("LINUX_DO_TOKEN is required to refresh connect token")
        self.logger.info(
            f"Refreshing connect token with linux_do_token (len={len(ld_token)})")
        try:
            connect = LinuxDoConnect(token=ld_token)
            t0 = time.perf_counter()
            await connect.login()
            self.logger.debug(f"linux.do login completed in {(time.perf_counter() - t0) * 1000:.0f}ms")

            self.logger.info("Successfully logged in to linux.do")

            try:
                connect_token, _ = await connect.get_connect_token()
                self.logger.info("Successfully obtained connect token from linux.do")
                return connect_token, ld_token
            except Exception as e:
                self.logger.error(f"Failed to extract connect token: {e}")
                raise
        except Exception as e:
            self.logger.error(f"LinuxDo login flow failed: {e}")
            raise

    async def get_valid_token(self) -> Optional[str]:
        tokens = load_tokens()
        sign_token = tokens.get("bohe_sign_token") or os.getenv("BOHE_SIGN_TOKEN")
        connect_token = tokens.get("linux_do_connect_token") or os.getenv("LINUX_DO_CONNECT_TOKEN")
        ld_token = tokens.get("linux_do_token") or os.getenv("LINUX_DO_TOKEN")

        if sign_token:
            self.logger.info("Verifying existing Bohe sign token...")
            t0 = time.perf_counter()
            valid, response_text = await self.sign_client.verify_token(sign_token)
            self.logger.debug(f"Token verification completed in {(time.perf_counter() - t0) * 1000:.0f}ms")
            if valid:
                self.logger.info("Existing Bohe sign token is still valid")
                return sign_token
            self.logger.warning("Stored Bohe sign token is invalid/expired, attempting to refresh...")

        for attempt in range(1, 4):
            try:
                if attempt > 1:
                    self.logger.info(f"Retrying token refresh (attempt {attempt}/3)...")

                if not connect_token or attempt > 1:
                    connect_token, ld_token = await self._get_connect_token(ld_token)

                t0 = time.perf_counter()
                new_token = await self.sign_client.get_token(connect_token)
                self.logger.debug(f"get_token completed in {(time.perf_counter() - t0) * 1000:.0f}ms")

                save_tokens(bohe_sign_token=new_token,
                            linux_do_connect_token=connect_token,
                            linux_do_token=ld_token)
                self.logger.info("Successfully obtained and saved new token")
                return new_token
            except RateLimitedError:
                # Upstream rate limit — exponential backoff with jitter
                if attempt == 3:
                    self.logger.error("All 3 attempts failed (rate limited). Giving up.")
                    raise
                backoff = min(300, 30 * (2 ** (attempt - 1)) + random.uniform(0, 10))
                self.logger.warning(
                    f"Rate limited on attempt {attempt}. "
                    f"Backing off {backoff:.0f}s before retry...")
                await asyncio.sleep(backoff)
            except Exception as e:
                self.logger.warning(f"Token refresh attempt {attempt} failed: {e}")
                if attempt == 3:
                    self.logger.error("All 3 attempts to refresh token failed.")
                    raise
                await asyncio.sleep(attempt * 2)
        return None

    async def sign(self, token: str) -> bool:
        try:
            self.logger.info("Checking check-in status...")
            t0 = time.perf_counter()
            status_r = await self.sign_client.get_checkin_status(token)
            self.logger.debug(f"Check-in status check completed in {(time.perf_counter() - t0) * 1000:.0f}ms, status={status_r.status_code}")
            if status_r.status_code == HTTPStatus.OK:
                status_data = status_r.json()
                if not status_data.get("can_spin"):
                    self.logger.info("Already checked in today (confirmed by server)")
                    return True
                self.logger.info("Ready to sign in, performing spin...")

            t0 = time.perf_counter()
            r = await self.sign_client.sign(token)
            self.logger.debug(f"Sign request completed in {(time.perf_counter() - t0) * 1000:.0f}ms, status={r.status_code}")

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
