# -*- coding: utf-8 -*-
# @Time    : 2023/8/17 下午7:28
# @Author  : sudoskys
# @File    : rabbit.py
# @Software: PyCharm
# !/usr/bin/env python
import atexit
import time

from pydantic import BaseModel


class Test(BaseModel):
    name: str
    age: int


import pika

# 创建凭证，使用rabbitmq用户密码登录
# 去邮局取邮件，必须得验证身份
credentials = pika.PlainCredentials("admin", "admin")
# 新建连接，这里localhost可以更换为服务器ip
# 找到这个邮局，等于连接上服务器
connection = pika.BlockingConnection(pika.ConnectionParameters('127.0.0.1', credentials=credentials))

# 创建频道
# 建造一个大邮箱，隶属于这家邮局的邮箱，就是个连接
channel = connection.channel()
# 声明一个队列，用于接收消息，队列名字叫“水许传”
channel.queue_declare(queue='水许传')
# 注意在rabbitmq中，消息想要发送给队列，必须经过交换(exchange)，初学可以使用空字符串交换(exchange='')，它允许我们精确的指定发送给哪个队列(routing_key=''),参数body值发送的数据
channel.basic_publish(exchange='',
                      routing_key='水许传',
                      body=Test(name="sudoskys", age=19).json())
print("已经发送了消息")
# 程序退出前，确保刷新网络缓冲以及消息发送给rabbitmq，需要关闭本次连接
time.sleep(100)


@atexit.register
def __clean():
    connection.close()
