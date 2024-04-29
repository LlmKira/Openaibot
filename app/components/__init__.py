from typing import Optional

from app.components.credential import Credential
from app.components.user_manager import USER_MANAGER


async def read_user_credential(user_id: str) -> Optional[Credential]:
    user = await USER_MANAGER.read(user_id=user_id)
    return user.credential
