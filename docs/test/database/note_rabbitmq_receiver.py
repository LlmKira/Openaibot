# -*- coding: utf-8 -*-
# @Time    : 2023/8/17 下午9:05
# @Author  : sudoskys
# @File    : rabbit_rev.py
# @Software: PyCharm
import pika
from pydantic import BaseModel

# 建立与rabbitmq的连接
credentials = pika.PlainCredentials("admin", "admin")
connection = pika.BlockingConnection(pika.ConnectionParameters('127.0.0.1', credentials=credentials))
channel = connection.channel()
channel.queue_declare(queue="水许传")


def callbak(ch, method, properties, body):
    class Test(BaseModel):
        name: str
        age: int
    print(Test.parse_raw(body))
    print("消费者接收到了任务：%r" % body.decode("utf8"))
    # 手动确认消息已经被消费
    ch.basic_ack(delivery_tag=method.delivery_tag)


# 有消息来临，立即执行callbak，没有消息则夯住，等待消息
# 老百姓开始去邮箱取邮件啦，队列名字是水许传
channel.basic_consume(on_message_callback=callbak, queue="水许传", auto_ack=False)
# 开始消费，接收消息
channel.start_consuming()
