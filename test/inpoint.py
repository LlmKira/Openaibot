# -*- coding: utf-8 -*-
# @Time    : 2023/9/18 下午9:35
# @Author  : sudoskys
# @File    : inpoint.py
# @Software: PyCharm
from arclet.alconna import Alconna, Option, Subcommand, Args

cmd = Alconna(
    "/pip",
    Subcommand("install", Option("-u|--upgrade"), Args.pak_name[str]),
    Option("list")
)

result = cmd.parse("/pip install ss numpy2 --upgrade")  # 该方法返回一个Arpamar类的实例
print(result.query('install'))
