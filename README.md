# Openaibot

OpenAI Chat Telegram Bot

[EN_README](https://github.com/sudoskys/Openaibot/blob/main/README.EN.md)

在 Telegram 上使用 OpenAi 写作

*目前只支持了文本对话*

*自制依赖库，没有做Api请求速率限制*

## 特性

* 支持私聊无感回复
* 支持速率限制
* 支持白名单系统
* 支持内容过滤
* (20221205)依赖库不支持异步，大量请求会阻塞,替换为自己的异步库

见 https://github.com/sudoskys/Openaibot/issues/1

## 初始化

* 拉取/更新程序

安装脚本会自动备份恢复配置，在根目录运行(不要在程序目录内)
，更新时候重新运行就可以备份程序了，如果是小更新可以直接 ``git pull``

```shell
curl -LO https://raw.githubusercontent.com/sudoskys/Openaibot/main/setup.sh && sh setup.sh
```

`cd Openaibot`

## 配置

### 配置 Redis

```shell
apt-get install redis
```

### 配置依赖

```bash
pip install -r requirements.txt
```

`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

### 过滤器

Danger.bin 一行一个黑名单词汇。至少要有一个。

### 配置 Config/app.toml

`cp app_exp.toml app.toml`

`vim app.toml`
`nano app.toml`

**配置文件**

```toml
[bot]
master = [100,200] # master user id &owner
botToken = 'key'
OPENAI_API_KEY = 'key'
INTRO = "POWER BY OPENAI"  # 后缀
ABOUT = "Created by github.com/sudoskys/Openaibot"

[proxy]
status = false
url = "http://127.0.0.1:7890"
```

[Telegram botToken申请](https://t.me/BotFather)

[OPENAI_API_KEY申请](https://beta.openai.com/account/api-keys)

## 运行

* 运行

```shell
nohup python3 main.py > /dev/null 2>&1 & 
```

* 查看进程

```shell
ps -aux|grep python3
```

* 终止进程
  后加进程号码

```shell
kill -9  
```

## 命令

**限制群组**

```
onw 白名单开
offw 白名单
open 开机器人
close 关机器人
usercold 用户冷却时间 ，1 为无限制
groupcold 群组冷却时间，1 为无限制
tokenlimit Api 的回复限制
inputlimit 输入prompt的限制
addw  加入白名单，/addw 111 222
delw  取消白名单，/delw 111 222
config See Config
```

**限制私聊**

```
userwon 用户白名单 开
userwoff 用户白名单 关
adduser 加入用户白名单
deluser 取消用户白名单
```

## 其他

Quick Dev by MVC 框架 https://github.com/TelechaBot/BaseBot