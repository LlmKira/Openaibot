# -*- coding: utf-8 -*-
# @Time    : 2023/8/18 下午7:08
# @Author  : sudoskys
# @File    : function.py
# @Software: PyCharm

__receiver__ = "llm_task"

import json
import os

from aio_pika.abc import AbstractIncomingMessage
from loguru import logger

from llmkira.middleware.chain_box import Chain, AuthReloader, ChainReloader
from llmkira.middleware.env_virtual import EnvManager
from llmkira.schema import RawMessage
from llmkira.sdk.func_calling.register import ToolRegister
from llmkira.sdk.schema import TaskBatch
from llmkira.task import Task, TaskHeader


class ChainFunc(object):
    @staticmethod
    async def reply_user(*,
                         platform: str,
                         task: TaskHeader,
                         text: str,
                         receiver: TaskHeader.Location
                         ):
        """
        通知用户
        :param platform: Default should be `task.receiver.platform`
        :param task: 任务 header
        :param text: 文本 str
        :param receiver: 接收者 TaskHeader.Location
        """
        # 通知用户
        return await Task.create_and_send(
            queue_name=platform,
            task=TaskHeader(
                sender=task.sender,
                receiver=receiver,
                task_meta=task.task_meta.reply_direct(chain_name=__receiver__),
                message=[
                    RawMessage(
                        user_id=task.receiver.user_id,
                        chat_id=task.receiver.chat_id,
                        text=text
                    )
                ]
            )
        )

    async def auth_chain(self,
                         *,
                         task: TaskHeader,
                         task_batch: TaskBatch
                         ):
        """
        认证链重发注册
        """
        _task_forward: TaskHeader = task.model_copy()
        meta: TaskHeader.Meta = _task_forward.task_meta.chain(
            name=__receiver__,
            write_back=False,  # 因为是发送给自己，所以不需要写回
            release_chain=True  # 要求释放链
        )
        """添加认证链并重置路由数据"""
        if meta.run_step_limit < meta.run_step_already:
            return logger.debug("Reject Invalid Request, Already Reach Limit")
        """拒绝不合法的请求"""
        meta.verify_uuid = meta.get_verify_uuid(task_batch=task_batch)
        # 注册本地部署点
        task_id = await AuthReloader(uid=_task_forward.receiver.uid).add_auth(
            chain=Chain(
                uuid=meta.verify_uuid,
                uid=_task_forward.receiver.uid,
                address=__receiver__,
                # 重要：转发回来这里
                arg=TaskHeader(sender=_task_forward.sender,
                               receiver=_task_forward.receiver,
                               task_meta=meta,
                               message=[]
                               )
            )
        )
        await self.reply_user(platform=_task_forward.receiver.platform,
                              receiver=_task_forward.receiver,
                              task=task,
                              text=f"🔑 Type `/auth {task_id}` to run `{task_batch.get_batch_name()}`"
                                   f"\ntry `!auth {task_id}` when no slash command"
                              )
        return logger.trace("Auth Chain Resign Success")

    async def resign_chain(
            self,
            task: TaskHeader, parent_func: str,
            repeatable: bool, deploy_child: int
    ):
        """
        子链孩子函数，请注意，此处为高风险区域，预定一下函数部署点位
        :param task: 任务
        :param parent_func: 父函数
        :param repeatable: 是否可重复
        :param deploy_child: 是否部署子链
        """
        _task_forward: TaskHeader = task.model_copy()
        # 添加认证链并重置路由数据
        meta: TaskHeader.Meta = _task_forward.task_meta.chain(
            name=__receiver__,
            write_back=True,
            release_chain=True
        )
        if meta.run_step_limit < meta.run_step_already:
            return logger.trace("Reject Invalid Request, Already Reach Limit")
        if deploy_child == 0:
            logger.debug(f"[112532] Function {parent_func} End its chain...")
            return logger.trace("Parent Function Reject Resign Its Child Chain")
        """拒绝不合法的请求"""
        _task_forward.task_meta = meta
        try:
            if not repeatable:
                _task_forward.task_meta.function_list = [
                    item
                    for item in _task_forward.task_meta.function_list
                    if item.name != parent_func
                ]
                logger.trace("Remove Used Function From Function List")
        except Exception as e:
            logger.error(e)
            logger.warning(f"[362211]Remove function {parent_func} failed")
        """拒绝不合法的请求"""
        # 注册本地部署点
        await ChainReloader(uid=_task_forward.receiver.uid).add_task(
            chain=Chain(
                uid=_task_forward.receiver.uid,
                address=_task_forward.receiver.platform,
                expire=60 * 60 * 2,
                arg=TaskHeader(
                    sender=_task_forward.sender,
                    receiver=_task_forward.receiver,
                    task_meta=meta,
                    message=[]
                )
            )
        )
        return logger.trace("Resign Chain Success")


class FunctionReceiver(object):
    """
    receive message from any platform
    """

    def __init__(self):
        self.task = Task(queue=__receiver__)

    @staticmethod
    async def run_pending_task(task: TaskHeader, pending_task: TaskBatch):
        """
        如果执行异常，必须抛出异常，否则会导致任务无法结束
        如果重发认证，不需要结束任务
        :param task: 任务
        :param pending_task: 待执行的函数
        :return: None
        """
        assert isinstance(pending_task, TaskBatch), "pending task type error"
        chain_func = ChainFunc()
        # Parse Function Call
        try:
            _arg = json.loads(pending_task.get_batch_args())
        except json.JSONDecodeError as decode_error:
            logger.warning("Function Arguments is not json format")
            await chain_func.reply_user(platform=task.receiver.platform,
                                        receiver=task.receiver,
                                        task=task,
                                        text=f"🔭 Sorry function `{pending_task.get_batch_name()}` "
                                             f"arguments is not json format"
                                             f"\narguments {pending_task.get_batch_args()}"
                                        )
            raise decode_error
        # Get Function Object
        _tool_cls = ToolRegister().get_tool(name=pending_task.get_batch_name())
        if not _tool_cls:
            logger.warning(f"Not found function {pending_task.get_batch_name()}")
            await chain_func.reply_user(platform=task.receiver.platform,
                                        receiver=task.receiver,
                                        task=task,
                                        text=f"🔭 Sorry function `{pending_task.get_batch_name()}` executor not found"
                                        )
            raise ModuleNotFoundError(f"Function {pending_task.get_batch_name()} not found")
        # Run Function
        _tool_obj = _tool_cls()
        if _tool_obj.require_auth:
            if task.task_meta.verify_uuid:
                # 是携带密钥的函数，是预先构建的可信任务头
                task.task_meta.verify_uuid = None
            else:
                # 需要认证，预构建携带密钥的待发消息并回退
                await chain_func.auth_chain(task=task,
                                            task_batch=pending_task
                                            )
                return logger.info(f"[Resign Auth] \n--auth-require {pending_task.get_batch_name()} require.")
        # 获取环境变量
        _env_dict = await EnvManager.from_uid(uid=task.receiver.uid).get_env_list(name_list=_tool_obj.env_required)
        assert isinstance(_env_dict, dict), "unexpected env dict? it should be dict..."
        # 运行函数, 传递模型的信息，以及上一条的结果的openai raw信息
        run_result = await _tool_obj.load(task=task,
                                          receiver=task.receiver,
                                          arg=_arg,
                                          env=_env_dict,
                                          pending_task=pending_task,
                                          refer_llm_result=task.task_meta.llm_result
                                          )
        # 当前节点要求生产或者任务完成
        if task.task_meta.resign_next_step or task.task_meta.is_complete:  # 路由
            await chain_func.resign_chain(task=task,
                                          parent_func=pending_task.get_batch_name(),
                                          repeatable=_tool_obj.repeatable,
                                          deploy_child=_tool_obj.deploy_child,
                                          )
        return run_result

    async def process_function_call(self, message: AbstractIncomingMessage
                                    ):
        """
        定位，解析，运行函数。要求认证，或申请结束/继续指标。
        :param message: message from queue
        :return: None
        """
        # Parse Message
        if os.getenv("LLMBOT_STOP_REPLY") == "1":
            return None
        task: TaskHeader = TaskHeader.model_validate_json(json_data=message.body.decode("utf-8"))
        # Get Function Call
        pending_task = await task.task_meta.work_pending_task(
            verify_uuid=task.task_meta.verify_uuid
        )
        if not pending_task:
            logger.trace("No Function Call")
            return None
        pending_task: TaskBatch
        logger.debug(f"Received A Batch FunctionRequest")
        try:
            await self.run_pending_task(task=task, pending_task=pending_task)
        except Exception as e:
            await task.task_meta.complete_task(task_batch=pending_task, run_result=e)
            logger.error(f"Function Call Error {e}")
            raise e
        finally:
            logger.trace("Function Call Finished")

    async def on_message(self,
                         message: AbstractIncomingMessage
                         ):
        """
        处理message
        :param message: message from queue
        :return: None
        """
        try:
            await self.process_function_call(message=message)
        except Exception as e:
            logger.error(f"Function Receiver Error {e}")
            await message.reject(requeue=False)
            raise e
        finally:
            await message.ack(multiple=False)

    async def function(self):
        logger.success("Receiver Runtime:Function Fork Cpu start")
        await self.task.consuming_task(self.on_message)
