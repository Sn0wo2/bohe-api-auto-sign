import asyncio
import sys

from client import BoheClient
from utils.logger import setup_logger

logger = setup_logger()


async def main():
    try:
        client = BoheClient()
        sign_token = await client.get_valid_token()

        if sign_token:
            await client.sign(sign_token)
        else:
            sys.exit(1)

    except Exception as e:
        logger.exception(f"Critical error in main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())