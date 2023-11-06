# -*- coding: utf-8 -*-
# @Time    : 2023/8/17 下午10:09
# @Author  : sudoskys
# @File    : ra.py
# @Software: PyCharm
import threading

import pika


class SingletonClass(object):
    """单例模式用来少创建连接"""
    # 加锁，防止并发较高时，同时创建对象，导致创建多个对象
    _singleton_lock = threading.Lock()

    def __init__(self, username='baibing', password='123456', ip='47.xxx.xxx.xx', port=5672, data={}):
        """__init__在new出来对象后实例化对象"""
        self.credentials = pika.PlainCredentials(username, password)
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=ip, port=port, credentials=self.credentials))
        self.channel = self.connection.channel()
        print('连接成功')

    def __new__(cls):
        """__new__用来创建对象"""
        if not hasattr(SingletonClass, "_instance"):
            with SingletonClass._singleton_lock:
                if not hasattr(SingletonClass, "_instance"):
                    SingletonClass._instance = super().__new__(cls)
        return SingletonClass._instance

    def callback(self, ch, method, properties, body):
        """订阅者的回调函数，可以在这里面做操作，比如释放库存等"""
        ch.basic_ack(delivery_tag=method.delivery_tag)  # ack机制，
        print("邮箱", body.decode())

    def connection_close(self):
        """关闭连接"""
        self.connection.close()

    def consuming_start(self):
        """等待消息"""
        self.channel.start_consuming()

    def this_publisher(self, email, queue_name='HELLOP'):
        """发布者
        email:消息
        queue_name：队列名称
        """

        # 1、创建一个名为python-test的交换机 durable=True 代表exchange持久化存储
        self.channel.exchange_declare(exchange='python', durable=True, exchange_type='direct')
        # self.channel.queue_declare(queue=queue_name)
        # 2、订阅发布模式,向名为python-test的交换机中插入用户邮箱地址email，delivery_mode = 2 声明消息在队列中持久化，delivery_mod = 1 消息非持久化
        self.channel.basic_publish(exchange='python',
                                   routing_key='OrderId',
                                   body=email,
                                   properties=pika.BasicProperties(delivery_mode=2)
                                   )

        print("队列{}发送用户邮箱{}到MQ成功".format(queue_name, email))
        # 3. 关闭连接
        self.connection_close()

    def this_subscriber(self, queue_name='HELLOP', prefetch_count=10):
        """订阅者
        queue_name：队列名称
        prefetch_count:限制未处理消息的最大值,ack未开启时生效
        """
        # 创建临时队列,队列名传空字符，consumer关闭后，队列自动删除
        result = self.channel.queue_declare('', durable=True, exclusive=True)

        # 声明exchange，由exchange指定消息在哪个队列传递，如不存在，则创建。durable = True 代表exchange持久化存储，False 非持久化存储
        self.channel.exchange_declare(exchange='python', durable=True, exchange_type='direct')

        # 绑定exchange和队列  exchange 使我们能够确切地指定消息应该到哪个队列去
        self.channel.queue_bind(exchange='python', queue=result.method.queue, routing_key='OrderId')

        self.channel.basic_consume(
            result.method.queue,
            self.callback,  # 回调地址(函数)
            auto_ack=False  # 设置成 False，在调用callback函数时，未收到确认标识，消息会重回队列。True，无论调用callback成功与否，消息都被消费掉
        )
        # 等待消息
        self.consuming_start()
