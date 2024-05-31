# -*- coding: utf-8 -*-
# @Time    : 2023/10/21 下午2:29
# @Author  : sudoskys
# @File    : event.py
# @Software: PyCharm

from pydantic import ConfigDict, BaseModel


def help_message():
    return """
*Command*

!chat - chat with me in a serious way :(
@<myname> - Chat with me in a simple way :)
!task - chat with function_enable
!ask - chat with function_disable
!auth - Auth a task

*Slash Command*

`/help` - Help message
`/tool` - Tool list
`/clear` - forget...you
`/auth` - activate a task (my power),but outside the thread
`/login` - login via url or raw
`/logout` - clear credential
`/env` - set environment variable, split by ; ,  use `/env ENV=NONE` to disable a env.
`/learn` - set your system prompt, reset by `/learn reset`

Make sure you invite me before you call me in channel, wink~

*DONT SHARE YOUR TOKEN/ENDPOINT PUBLIC!*

- Please confirm that that bot instance is secure, some plugins may be dangerous on unsafe instance.
"""


class SlashCommand(BaseModel):
    """
    https://api.slack.com/interactivity/slash-commands#app_command_handling
    token=gIkuvaNzQIHg97ATvDxqgjtO
    &team_id=T0001
    &team_domain=example
    &enterprise_id=E0001
    &enterprise_name=Globular%20Construct%20Inc
    &channel_id=C2147483705
    &channel_name=test
    &user_id=U2147483697
    &user_name=Steve
    &command=/weather
    &text=94070
    &response_url=https://hooks.slack.com/commands/1234/5678
    &trigger_id=13345224609.738474920.8088930838d88f008e0
    &api_app_id=A123456
    """

    token: str = None
    team_id: str = None
    team_domain: str = None
    enterprise_id: str = None
    enterprise_name: str = None
    channel_id: str = None
    channel_name: str = None
    user_id: str = None
    user_name: str = None
    command: str = None
    text: str = None
    response_url: str = None
    trigger_id: str = None
    api_app_id: str = None
    model_config = ConfigDict(extra="allow")


class SlackChannelInfo(BaseModel):
    id: str = None
    name: str = None
    is_channel: bool = None
    is_group: bool = None
    is_im: bool = None
    is_mpim: bool = None
    is_private: bool = None
    created: int = None
    is_archived: bool = None
    is_general: bool = None
    unlinked: int = None
    name_normalized: str = None
    is_shared: bool = None
    is_org_shared: bool = None
    is_pending_ext_shared: bool = None
    pending_shared: list = None
    context_team_id: str = None
    updated: int = None
    parent_conversation: str = None
    creator: str = None
    is_ext_shared: bool = None
    shared_team_ids: list = None
    pending_connected_team_ids: list = None
    is_member: bool = None
    last_read: str = None
    topic: dict = None
    purpose: dict = None
    previous_names: list = None
    model_config = ConfigDict(extra="allow")
