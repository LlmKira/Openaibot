from hashlib import md5
from io import BytesIO
from typing import Union, Optional

from pydantic import BaseModel, Field

from llmkira._exception import CacheDatabaseError
from llmkira.kv_manager._base import KvManager

FILE_EXPIRE_TIME = 60 * 60 * 24
MAX_UPLOAD_FILE_SIZE = 15 * 1024 * 1024  # 15MB


def generate_file_md5(
    data: Union[str, bytes, BytesIO], length: int = 8, upper: bool = True
) -> str:
    """
    # WARNING: This function is not suitable for BIG files.
    Generate a unique short MD5 Hash.
    :param data: The data to be hashed.
    :param length: The desired length of the hashed object; it must be between 1 and 32 (inclusive).
    :param upper: Flag denoting whether to return the hash in uppercase (default is True).
    :return: A unique short digest of the hashed object.
    :raises AssertionError: If length is not within the range 1-32 inclusive.
    """

    assert (
        0 < length <= 32
    ), "length must be less than or equal to 32 and more than zero."

    hash_md5 = md5()

    if isinstance(data, str):
        hash_md5.update(data.encode("utf-8"))
    elif isinstance(data, bytes):
        hash_md5.update(data)
    elif isinstance(data, BytesIO):
        for chunk in iter(lambda: data.read(4096), b""):
            hash_md5.update(chunk)

    # Generate the MD5 hash.
    digest = hash_md5.hexdigest()
    # Shorten to the required length and uppercase if necessary.
    short_id = digest[:length].upper() if upper else digest[:length]
    return short_id


class File(BaseModel):
    creator: str = Field(description="创建用户")
    file_name: str = Field(description="文件名")
    file_key: str = Field(description="文件 Key")
    caption: Optional[str] = Field(default=None, description="文件描述")

    async def download_file(self) -> Optional[bytes]:
        """
        Download the file from the cache.
        If the file is not found in the cache, the method will return None.
        :return: The file data if found, otherwise None.
        """
        return await GLOBAL_FILE_HANDLER.download_file(self.file_key)

    @classmethod
    async def upload_file(
        cls, creator: str, file_name: str, file_data: Union[bytes, BytesIO]
    ) -> "File":
        """
        Upload a file to the cache.
        If file_data is greater than the size limit (15MB), a CacheDatabaseError will be raised.
        :param creator: The creator of the file.
        :param file_name: The name of the file.
        :param file_data: The file to be uploaded, either a bytes object or a BytesIO stream.
        :return: A File object representing the uploaded file.
        :raises CacheDatabaseError: If the file size exceeds the limit of 15MB.
        """
        file_key = await GLOBAL_FILE_HANDLER.upload_file(file_data)
        return cls(creator=creator, file_name=file_name, file_key=file_key)


class FileHandler(KvManager):
    def prefix(self, key: str) -> str:
        return f"file:{key}"

    async def upload_file(
        self,
        file_data: Union[bytes, BytesIO],
    ) -> str:
        """
        Upload a file to the cache, and return its unique ID.
        The file_data argument is the file to be uploaded, either a bytes object or a BytesIO stream.
        If file_data is greater than the size limit (15MB), a CacheDatabaseError will be raised.
        The method will return the unique ID for the uploaded file.
        :param file_data: The file to be uploaded.
        :return: The unique ID of the uploaded file.
        :raises CacheDatabaseError: If the file size exceeds the limit of 15MB.
        """

        if isinstance(file_data, BytesIO):
            file_data = file_data.read()

        if len(file_data) > MAX_UPLOAD_FILE_SIZE:
            raise CacheDatabaseError("File size exceeds the limit of 15MB")

        file_id = generate_file_md5(file_data)
        await self.save_data(file_id, file_data, timeout=FILE_EXPIRE_TIME)
        return file_id

    async def download_file(self, file_id: str) -> Optional[bytes]:
        """
        Download a file identified by file_id from the cache.
        If the file is not found in the cache, the method will return None.
        :param file_id: The unique ID of the file to be downloaded.
        :return: The file data if found, otherwise None.
        """
        result = await self.read_data(file_id)
        return result


GLOBAL_FILE_HANDLER = FileHandler()
