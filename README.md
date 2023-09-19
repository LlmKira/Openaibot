# LLMBot

![Docker Image Size (tag)](https://img.shields.io/docker/image-size/sudoskys/llmbot/latest)
![Docker Image Version (latest semver)](https://img.shields.io/docker/v/sudoskys/llmbot)
![docker workflow](https://github.com/llmkira/llmbot/actions/workflows/docker-ci.yaml/badge.svg)

[English_Readme](README_EN.md)

LLMBot 是基于消息队列的机器人助手，可以装载插件完成许多功能。为 Gpt Func Call 和 广播机制的验证项目。

与 `OpenaiBot` 项目不同的是，此项目尝试基于 消息平台 复刻 ChatGpt 的插件系统。实现部分或更进一步的功能。

此项目的绝大多数功能都可以由插件完成。

> 因为 func call 为 feature,所以只支持 Openai 类型的 api, 不打算支持没有 func call 的 LLM

## 📦 Feature

- 📦 中间件/插件系统，可以自由扩展
- 📝 消息系统，脱离平台和时间限制
- 📎 订阅系统，可以订阅多个发送者
- 📬 自定义 ApiKey 和 后端
- 🍾 简洁交互设计，避免繁琐的权限验证
- 🎵 细化的消费记录
- 🍰 联网插件实现

### 🧀 部分插件预览

| Sticker Converter                   | Timer Func                      |
|-------------------------------------|---------------------------------|
| ![sticker](./docs/sticker_func.gif) | ![timer](./docs/timer_func.gif) |

```python3
__plugin_name__ = "set_alarm_reminder"

alarm = Function(name=__plugin_name__, description="Set a timed reminder")
alarm.add_property(
    property_name="delay",
    property_description="The delay time, in minutes",
    property_type="integer",
    required=True
)
alarm.add_property(
    property_name="content",
    property_description="reminder content",
    property_type="string",
    required=True
)
```

## 📝 部署指南

请确认您的系统为UTF8，`dpkg-reconfigure locales`

### Docker

```shell
docker-compose -f docker-compose.yml -p llmbot up -d llmbot --compatibility
```

### PM2

````
apt install npm
npm install pm2 -g
pm2 start pm2.json
````

### Shell

- (可选) 解决冲突

`pip uninstall llm-kira`

- 🛠 配置 `.env` 文件

```bash
cp .env.example .env
nano .env

```

- ⚙️ 安装依赖

```bash
pip install -r requirements.txt
```

- 🗄 配置数据库环境

```bash
# 安装 Redis
apt-get install redis
systemctl enable redis.service --now
```

```bash
# 安装 RabbitMQ
docker pull rabbitmq:3.10-management
docker run -d -p 5672:5672 -p 15672:15672 \
        -e RABBITMQ_DEFAULT_USER=admin \
        -e RABBITMQ_DEFAULT_PASS=admin \
        --hostname myRabbit \
        --name rabbitmq \
        rabbitmq:3.10-management 
docker ps -l
```  

- ▶️ 运行

```bash
python3 start_sender.py
python3 start_receiver.py

```

## 基础命令

```shell
help - 帮助
chat - 聊天
task - 任务
tool - 工具列表
bind - 绑定可选平台
unbind - 解绑可选平台
clear - 删除自己的记录
rset_endpoint - 自定义后端
rset_key - 设置openai
clear_rset - 抹除自定义设置

```

## TODO

- [x] 插件系统
- [x] 定时系统
- [x] 订阅系统
- [x] 插件的文件支持
- [x] 插件的Openai支持
- [ ] 用户拉黑插件
- [x] 消费系统完善
- [ ] 图表示例插件
- [ ] 插件管理器
- [ ] 多 LLM 调度

## 架构一览

````
.
├── cache # 缓存
├── docs # 开发手记
├── middleware
│     ├── __init__.py
│     ├── llm_task.py # 任务模型
│     ├── router  # 路由/订阅系统
│     └── user  # 用户自定义设置
├── plugins # 插件系统
├── plugins_manager.py
├── README.md
├── receiver # 收端
├── requirements.txt
├── run.log
├── schema.py
├── sdk  # sdk
│     ├── endpoint
│     ├── error.py
│     ├── func_call.py
│     ├── __init__.py
│     ├── memory
│     ├── network.py
│     ├── schema.py
│     └── utils.py
├── sender # 发端
├── setting
│     ├── __init__.py
│     ├── task.py
│     └── telegram.py
├── start_receiver.py
├── start_sender.py
├── task # 任务系统 / 核心模组
├──── __init__.py
````

## 💻 如何开发？

插件开发请参考 `plugins` 目录下的示例插件。

## 🤝 如何贡献？

欢迎提交 Pull Request，我们非常乐意接受您的贡献！请确保您的代码符合我们的代码规范，并附上详细的说明。感谢您的支持和贡献！ 😊
