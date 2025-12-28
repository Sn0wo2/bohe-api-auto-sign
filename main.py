import asyncio
import os
import sys
import traceback
from typing import Callable, Awaitable, Tuple, Optional

from curl_cffi.requests import AsyncSession
from linux_do_connect import LinuxDoConnect

from bohe_api.login import get_api_session, verify_bohe_api_token
from bohe_sign.login import verify_bohe_token, get_sign_token
from store.token import load_tokens, save_tokens
from utils.logger import setup_logger

logger = setup_logger()


async def _refresh_linux_do_connect_token(linux_do_token: str) -> tuple[str, str]:
    logger.info("Refreshing LINUX_DO_CONNECT_TOKEN...")
    client = LinuxDoConnect(token=linux_do_token)
    return await (await client.login()).get_connect_token()


async def _get_or_refresh_generic_token(
    token_key: str,
    token_name: str,
    verify_func: Callable[[str, Optional[str]], Awaitable[Tuple[bool, str]]],
    acquire_func: Callable[[str], Awaitable[str]]
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    tokens = load_tokens()
    target_token = tokens.get(token_key)
    connect_token = tokens.get("linux_do_connect_token")
    ld_token = tokens.get("linux_do_token") or os.getenv("LINUX_DO_TOKEN")

    if target_token:
        try:
            is_valid, msg = await verify_func(target_token, connect_token)
            if is_valid:
                logger.info(f"Using stored valid {token_name}")
                logger.debug(f"Validation response: {msg}")
                return target_token, connect_token, ld_token
            logger.warning(f"{token_name} invalid: {msg}")
        except Exception as e:
            logger.warning(f"Error verifying stored {token_name}: {e}")

    if not ld_token and not connect_token:
        logger.error("No LINUX_DO_TOKEN available for login.")
        return target_token, connect_token, ld_token

    has_refreshed_connect = False

    if not connect_token:
        try:
            connect_token, ld_token = await _refresh_linux_do_connect_token(ld_token)
            has_refreshed_connect = True
        except Exception as e:
            logger.error(f"Failed to obtain initial connect token: {e}")
            return target_token, connect_token, ld_token

    new_token = ""
    try:
        new_token = await acquire_func(connect_token)
    except Exception as e:
        logger.warning(f"Failed to acquire {token_name} with current connect token: {e}")

    if not new_token and not has_refreshed_connect and ld_token:
        try:
            logger.info("Connect token might be expired, attempting refresh and retry...")
            connect_token, ld_token = await _refresh_linux_do_connect_token(ld_token)
            new_token = await acquire_func(connect_token)
        except Exception as e:
            logger.error(f"Failed retry with new connect token: {e}")
            traceback.print_tb(e.__traceback__)

    if not new_token:
        logger.error(f"Failed to obtain {token_name} after all attempts")
        return target_token, connect_token, ld_token

    logger.info(f"Successfully obtained new {token_name}")

    save_kwargs = {
        token_key: new_token,
        "linux_do_connect_token": connect_token,
        "linux_do_token": ld_token
    }
    save_tokens(**save_kwargs)

    return new_token, connect_token, ld_token


async def _verify_api_token_wrapper(token: str, connect_token: Optional[str]) -> Tuple[bool, str]:
    if not connect_token:
        return False, "Missing connect_token for session creation"
    
    session = AsyncSession()
    session.cookies.set("session", token, domain="x666.me")
    return await verify_bohe_api_token(session)


async def _verify_sign_token_wrapper(token: str, _: Optional[str]) -> Tuple[bool, str]:
    return await verify_bohe_token(token)


async def _acquire_api_token_wrapper(connect_token: str) -> str:
    session = await get_api_session(connect_token=connect_token)
    is_valid, msg = await verify_bohe_api_token(session)
    if is_valid:
        token = session.cookies.get("session", domain="x666.me")
        if token:
            return token
        raise ValueError("Session cookie not found after successful verification")
    raise ValueError(f"Acquired API session invalid: {msg}")


async def get_or_refresh_api_token() -> tuple[Optional[str], Optional[str], Optional[str]]:
    return await _get_or_refresh_generic_token(
        token_key="bohe_api_token",
        token_name="BOHE_API_TOKEN",
        verify_func=_verify_api_token_wrapper,
        acquire_func=_acquire_api_token_wrapper
    )


async def get_or_refresh_sign_token() -> tuple[Optional[str], Optional[str], Optional[str]]:
    return await _get_or_refresh_generic_token(
        token_key="bohe_sign_token",
        token_name="BOHE_SIGN_TOKEN",
        verify_func=_verify_sign_token_wrapper,
        acquire_func=get_sign_token
    )


async def main():
    try:
        sign_token, _, _ = await get_or_refresh_sign_token()

        if sign_token:
            logger.info("Successfully obtained Bohe Token")
        else:
            logger.error("Failed to obtain Bohe Token")
            sys.exit(1)

        api_token, _, _ = await get_or_refresh_api_token()

        if api_token:
            logger.info("Successfully obtained API Token")
        else:
            logger.error("Failed to obtain API Token")
            sys.exit(1)

    except Exception as e:
        logger.exception(f"Critical error in main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())