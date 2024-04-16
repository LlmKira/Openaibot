import time

from pydantic import Field, BaseModel, ConfigDict


class Event(BaseModel):
    thead_uuid: str = Field(description="Thead UUID")
    by_platform: str = Field(description="创建平台")
    by_user: str = Field(description="创建用户")
    expire_at: int = Field(default=60 * 60 * 24 * 1, description="expire")
    create_at: int = Field(
        default_factory=lambda: int(time.time()), description="created_times"
    )
    model_config = ConfigDict(extra="ignore", arbitrary_types_allowed=False)
