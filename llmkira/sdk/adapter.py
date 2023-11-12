# -*- coding: utf-8 -*-
# @Time    : 2023/11/9 下午4:29
# @Author  : sudoskys
# @File    : adapter.py
# @Software: PyCharm
from typing import List, Type, Optional, Literal
from typing import TYPE_CHECKING

from loguru import logger
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .endpoint.schema import LlmRequest, LlmResult
    # from .endpoint.tokenizer import BaseTokenizer


class SingleModel(BaseModel):
    llm_model: str
    token_limit: int
    func_executor: Literal["function_call", "tool_call", "unsupported"]
    request: Type["LlmRequest"]
    response: Type["LlmResult"]
    schema_type: str
    exception: Optional[str] = Field(None, description="exception")


class ModelMeta(object):
    """
    第三方管理分发模型相关的操作类
    """
    model_list: List[SingleModel] = []

    def add_model(self, models: List[SingleModel]):
        for model in models:
            if not model.exception:
                logger.debug(f"🥐 [Model Available] {model.llm_model}")
            self.model_list.append(model)

    def get_by_model_name(self,
                          *,
                          model_name: str
                          ) -> SingleModel:
        for model in self.model_list:
            if model.llm_model == model_name:
                if model.exception:
                    raise NotImplementedError(
                        f"model {model_name} not implemented"
                        f"exception: {model.exception}"
                    )
                return model
        raise LookupError(
            f"model {model_name} not found! "
            f"please check your model name"
        )

    def get_model_list(self):
        return [model.llm_model for model in self.model_list]

    def get_token_limit(self,
                        *,
                        model_name: str
                        ) -> int:
        return self.get_by_model_name(
            model_name=model_name
        ).token_limit

    def get_schema_model_group(self,
                               *,
                               schema_type: str
                               ) -> List[SingleModel]:
        return [
            model for model in self.model_list
            if model.schema_type == schema_type
        ]


SCHEMA_GROUP = ModelMeta()
