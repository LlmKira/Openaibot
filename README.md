# Openaibot

OpenAI Chat Bot

## 配置

### 配置 Redis

```shell
apt-get install redis
```

### 配置依赖

`pip install -r requirements.txt`

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
master = [100]
botToken = 'key'
OPENAI_API_KEY = 'key'
INTRO = "POWER BY OPENAI"
ABOUT = "Created by github.com/sudoskys/Openaibot"

[proxy]
status = false
url = "http://127.0.0.1:7890"

```