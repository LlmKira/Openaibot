import asyncio
import json
from typing import Union, Optional

import lmdb
from loguru import logger

from .runtime_schema import AbstractDataClass, PREFIX


class LMDBClientAsyncWrapper(AbstractDataClass):
    """
    LMDB 数据基类
    """

    def __init__(self, backend, prefix=PREFIX):
        self.prefix = prefix
        self.env = lmdb.open(backend)
        self.lock = asyncio.Lock()

    async def ping(self):
        return True

    def update_backend(self, backend):
        self.env = lmdb.open(backend)
        return True

    async def read_data(self, key) -> Optional[Union[dict, str, bytes]]:
        """
        Read data from LMDB
        """
        data = None
        async with self.lock:
            with self.env.begin() as txn:
                raw_data = txn.get((self.prefix + str(key)).encode())
                if raw_data is not None:
                    try:
                        data = json.loads(raw_data.decode())
                    except json.JSONDecodeError:
                        # 如果JSON解码失败，并且数据以一个utf8字符串开头，我们假定数据是字符串
                        if raw_data.startswith(b'{"') is False:
                            data = raw_data.decode()
                    except UnicodeDecodeError:
                        # 如果Unicode解码失败，我们假定数据是字节型数据
                        data = raw_data
                    except Exception as ex:
                        logger.trace(ex)
        return data

    async def set_data(self, key, value: Union[dict, str, bytes], timeout: int = None):
        """
        Set data to LMDB
        :param key:
        :param value: a dict, str or bytes
        :param timeout: seconds
        :return:
        """
        async with self.lock:
            with self.env.begin(write=True) as txn:
                if isinstance(value, (dict, list)):
                    value = json.dumps(value).encode()
                elif isinstance(value, str):
                    # 如果数据是一个字符串，我们将其编码为字节数据
                    value = value.encode()
                # 对于字节类型的数据，我们直接存储
                txn.put((self.prefix + str(key)).encode(), value)
        return True
