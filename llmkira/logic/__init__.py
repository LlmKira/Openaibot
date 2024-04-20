from typing import Optional

from loguru import logger
from pydantic import BaseModel, Field, SecretStr

from llmkira.openai.cell import UserMessage
from llmkira.openai.request import OpenAI, OpenAICredential


class whether(BaseModel):
    """
    Decide whether to agree to the decision based on the content
    """

    yes_no: bool = Field(description="Whether the condition is true or false")
    comment_to_user: Optional[str] = Field(
        default="", description="Comment on the decision"
    )


class continue_act(BaseModel):
    """
    Decide whether to continue execution based on circumstances
    """

    continue_it: bool = Field(description="Whether to continue execution")
    comment_to_user: Optional[str] = Field(
        default="", description="Comment on the decision"
    )


class LLMLogic(object):
    """
    LLMLogic is a class that provides some basic logic operations.

    """

    def __init__(self, api_endpoint, api_key, api_model):
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.api_model = api_model

    async def llm_if(self, context: str, condition: str, default: bool):
        message = f"Context:{context}\nCondition{condition}\nPlease make a decision."
        try:
            logic_if = await OpenAI(
                model=self.api_model, messages=[UserMessage(content=message)]
            ).extract(
                response_model=whether,
                session=OpenAICredential(
                    api_key=SecretStr(self.api_key),
                    base_url=self.api_endpoint,
                    model=self.api_model,
                ),
            )
            logic_if: whether
            return logic_if
        except Exception as e:
            logger.error(f"llm_if error: {e}")
            return whether(yes_no=default)

    async def llm_continue(self, context: str, condition: str, default: bool):
        message = f"Context:{context}\nCondition{condition}\nPlease make a decision whether to continue."
        try:
            logic_continue = await OpenAI(
                model=self.api_model, messages=[UserMessage(content=message)]
            ).extract(
                response_model=continue_act,
                session=OpenAICredential(
                    api_key=SecretStr(self.api_key),
                    base_url=self.api_endpoint,
                    model=self.api_model,
                ),
            )
            logic_continue: continue_act
            return logic_continue
        except Exception as e:
            logger.error(f"llm_continue error: {e}")
            return continue_act(continue_it=default)
