# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 下午9:40
# @Author  : sudoskys
# @File    : event.py
# @Software: PyCharm

def help_message():
    return """
    /help - 帮助
    /chat - 聊天
    /task - 任务
    /tool - 工具列表
    /clear - 删除自己的记录
    /auth - 授权
    
Private Chat Only:
    /bind - 绑定可选平台
    /unbind - 解绑可选平台
    /set_endpoint - 自定义后端
    /clear_endpoint - 抹除自定义设置
    /env - 配置变量

!Please confirm that that bot instance is secure, some plugins may be dangerous on unsafe instance.
"""
