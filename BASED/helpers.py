import logging
import os
from asyncio import get_running_loop
from concurrent.futures import ThreadPoolExecutor
from typing import Never, NoReturn

import BASED.conf as conf

logger = logging.getLogger(__name__)


def assert_never(_: Never) -> NoReturn:
    raise AssertionError("Expected to be unreachable")


def get_default(obj, keys: list, default):
    try:
        current_value = obj
        for key in keys:
            current_value = current_value[key]
        if current_value is None:
            return default
        return current_value
    except Exception:
        return default


def create_storage_folders():
    folders = []
    for folder in folders:
        path = os.path.join(conf.STORAGE_DIR, folder)
        isExist = os.path.exists(path)
        if not isExist:
            logger.info("Create storage folder %s", folder)
            os.makedirs(path)


async def run_in_executor(func: (...), executor: ThreadPoolExecutor, *args):
    loop = get_running_loop()
    result = await loop.run_in_executor(executor, func, *args)
    return result
