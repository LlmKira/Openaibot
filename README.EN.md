# Openaibot

OpenAI Chat Telegram Bot

[EN_README](https://github.com/sudoskys/Openaibot/blob/main/README.EN.md)

Writing with OpenAi on Telegram

*Only text conversations are currently supported*

*Homebrew dependency library, no Api request rate limiting done*

## Features

* Support for unsensitive replies to private chats
* Support for rate limiting
* Support for whitelist system
* Support for content filtering
* (20221205) Dependency library does not support asynchronous, large number of requests will block, replace with own asynchronous library

See https://github.com/sudoskys/Openaibot/issues/1

## Initialization

* Pull/update process

The install script will automatically backup and restore the configuration, run it in the root directory (not in the program directory)
If it's a small update you can just ``git pull``.

```shell
curl -LO https://raw.githubusercontent.com/sudoskys/Openaibot/main/setup.sh && sh setup.sh
```

``cd Openaibot``

## Configure

### Configure Redis

```shell
apt-get install redis
```

### Configure dependencies

```bash
pip install -r requirements.txt
```

``pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple``

### Filters

Danger.bin One line of one blacklisted vocabulary. At least one.

### Config/app.toml

`cp app_exp.toml app.toml`

`vim app.toml`
`nano app.toml`

**configuration file**

``toml
[bot]
master = [100,200] # master user id &owner
botToken = 'key'
OPENAI_API_KEY = 'key'
INTRO = "POWER BY OPENAI"
ABOUT = "Created by github.com/sudoskys/Openaibot"
WHITE = "Group NOT in WHITE list"

[proxy]
status = false
url = "http://127.0.0.1:7890"
```

[Telegram botToken request](https://t.me/BotFather)

[OPENAI_API_KEY request](https://beta.openai.com/account/api-keys)

## Run

* Run

```shell
nohup python3 main.py > /dev/null 2>&1 & 
```

* View the process

```shell
ps -aux|grep python3
```

* Terminate a process
  followed by the process number

```shell
kill -9  
```

## command

**restrict group**

```
onw whitelist on
offw whitelist
open open bot
close close bot
usercold User cooldown, 1 for unlimited
groupcold Group cooldown time, 1 for unlimited
tokenlimit Api reply limit
inputlimit Limit on input prompts
addw add to whitelist, /addw 111 222
delw Remove whitelist, /delw 111 222
config See Config
```

**limit private chat**

```
userwon user whitelist on
userwoff User whitelist Off
adduser Add user to whitelist
deluser un-whitelist users
```

## Other

Quick Dev by MVC framework https://github.com/TelechaBot/BaseBot

