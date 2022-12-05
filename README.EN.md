# Openaibot

OpenAI Chat Telegram Bot


## Initialization

* Pull/update the program

The install script automatically backs up and restores the configuration, run it in the root directory (not in the
program directory)
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
master = [100] # your user id
botToken = 'key'  
OPENAI_API_KEY = 'key'
INTRO = "POWER BY OPENAI" # Suffix
ABOUT = "Created by github.com/sudoskys/Openaibot"

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

```
onw whitelist on
offw whitelist
open turn on the bot
close turn off the bot
usercold user cool , 1 for unlimited
groupcold Group cooling, 1 for unlimited
tokenlimit Api reply limit
inputlimit Limit on input prompts
addw add to whitelist, /addw 111 222
delw to un-whitelist, /delw 111 222
```

Quick Dev by MVC framework https://github.com/TelechaBot/BaseBot