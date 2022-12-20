![cover](https://raw.githubusercontent.com/sudoskys/Openaibot/main/docs/covers.png)


------------------------------------
<p align="center">
  <img alt="License" src="https://img.shields.io/badge/LICENSE-Other-ff69b4">
  <img src="https://img.shields.io/badge/Python-3.7|8|9|10-green" alt="PYTHON" >
  <a href="https://afdian.net/a/Suki1077"><img src="https://img.shields.io/badge/Buyme-milk-DB94A2" alt="SPONSOR"></a>
  <a href="https://app.fossa.com/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot?ref=badge_small" alt="FOSSA Status"><img src="https://app.fossa.com/api/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot.svg?type=small"/></a>
</p>

<h2 align="center">OpenaiBot</h2>

OpenAI Chat Bot For Telegram. 在 Telegram 上使用 OpenAi 交互。

[EN_README](https://github.com/sudoskys/Openaibot/blob/main/README.EN.md)

本项目利用 `Api` 认证 `Token` + 上下文记忆池来实现 chat ，并不是 `chatGPT` 的逆向，类 chatGPT 的 **Python 实现** 由本机器人自实现。

*复刻的 chatGPT ，体验基本一样 (?)，就是 Api 要钱*

*自制异步依赖库提速，自制上下文优化策略*

[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot.svg?type=large)](https://app.fossa.com/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot?ref=badge_large)

## 特性

* 聊天 (chat) chatGpt 自实现 + NLP 增强
* 续写 (write)  独立推测，续写
* 设定固定头人设
* 多主人管理
* 多 Api key 负载，超额弹出。
* chatGPT api 版本实现，不逆向 preview 的 api
* 支持私聊
* 支持群聊
* 支持速率限制
* 支持用量管理
* 支持白名单系统
* 支持黑名单系统
* 支持内容过滤
* (20221205) 依赖库不支持异步，大量请求会阻塞，替换为自己写的异步库
* chatGpt 替换为自己写的 chatGpt Openai api Python 实现
* 动态裁剪上下文，防止超额
* 网络中间件支持， Prompt Injection，对Chat更友好

见 https://github.com/sudoskys/Openaibot/issues/1

**聊天**

🔭利用 `/chat + 句子` 发起对话，然后**只需要回复**可交谈。私聊消息 或 群组 48 小时内的消息，会自动使用上下文进行推测和裁剪，直接回复就可以继续对话。

**重置**

每次使用`/forgetme` 都会重置 Ai 的记忆桶。

**续写**

🥖使用 `/write` 进行没有上下文推测的续写。

**Head**

支持场景设置，采用 `/remind` 设计自己的请求头。例如 `Ai 扮演在空间站的宇航员`。设定小于 4 个字符会使用默认值。

*这些设定的说明*

发送到 Api 的格式：

```markdown
head（不写默认为 下面的对话是人和 Ai 助手的对话）
nlp 处理后的关键对话
保留的上文三条原始消息
启动头 (AI:)
```

## 初始化

* 本地拉取/更新程序

安装脚本会自动备份恢复配置，在根目录运行（不要在程序目录内）
，更新时候重新运行就可以备份程序了，如果是小更新可以直接 ``git pull``。

```shell
curl -LO https://raw.githubusercontent.com/sudoskys/Openaibot/main/setup.sh && sh setup.sh
```

`cd Openaibot`

* [Docker](https://hub.docker.com/r/sudoskys/openaibot)

Docker 镜像在保证情况 stable 后才会发布更新。

```bash
git clone https://github.com/sudoskys/Openaibot
cd Openaibot
vim Config/service.json # 见下面
docker compose up -d
```

## 配置

### 配置 Redis

**本机**

```shell
apt-get install redis
```

**Docker**

配置 `service.json` ， 样板示例在下面，需要将 `localhost` 改为 `redis`

### 配置依赖

```bash
pip install -r requirements.txt
```

`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

### 过滤器

Data/Danger.form 一行一个黑名单词汇。至少要有一个。

如果没有，程序会自动下拉云端默认名单，后续的 updetect 也会拉云端覆盖本地。

你可以通过放置一个一行的名单来关闭这个过滤器，但是我不赞成你这样做。

### 配置 Config/app.toml

`cp app_exp.toml app.toml`

`vim app.toml`
`nano app.toml`

**配置文件**

```toml
[bot]
master = [100, 200] # master user id , 账号 ID
botToken = 'key' # 机器人密钥
INTRO = "POWER BY OPENAI"  # 后缀
ABOUT = "Created by github.com/sudoskys/Openaibot" # 关于命令返回
WHITE = "Group NOT in WHITE list" # 黑白名单提示
Enhance_Server = { "https://www.expserver.com?q={}" = "auto", "http:/exp?q={}" = "auto" }
# 联网中间件支持，自己找 server,{}将被替换为搜索词,目前联网回答的标识键为 Auto

# 设置的代理，但是不代理 openai api, 只代理 bot
[proxy]
status = false
url = "http://127.0.0.1:7890"
```

[Telegram botToken 申请](https://t.me/BotFather)

### 配置 key

在机器人私聊中配置 key

```markdown
see_api_key - 现在几个 Api key
del_api_key - 删除 Api key
add_api_key - 增加 Api key
```

[OPENAI_API_KEY 申请](https://beta.openai.com/account/api-keys)，支持多 key 分发负载。
[定价参考](https://openai.com/api/pricing/)。

请不要向任何人暴露你的 `app.toml`

### 配置 `service.json`

在 `Config/service.json` 下面。如果没有此文件，会使用默认值。如果有会深度覆盖。不会补全预设中没有的键。

```json
{
  "redis": {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "password": null
  },
  "tts": {
    "status": false,
    "type": "vits",
    "vits": {
      "api": "http://127.0.0.1:9557/tts/generate",
      "limit": 20,
      "model_name": "some.pth",
      "speaker_id": 1
    }
  }
}
```

redis:

- ?

tts:

- status 开关
- type 类型
- vits:limit 长度内的文本会被转换
- vits:model_name 模型名字，some.pth,在 model 文件夹下的
- vits:speaker_id 说话人的ID,具体看模型config

#### VITS 语音支持说明(ONLY CN NOW)

这项技术提供了一种仿真的语音交互技术。

Api 后端为我打包改造的 MoeGoe https://github.com/sudoskys/MoeGoe

安装依赖，运行 `server.py` 文件可以默认使用。

模型下面请查询 MoeGoe 项目的 Readme,并注意模型相应的协议。

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
kill -9 id
```

## 命令

限制类设置设定为 `1` 代表不生效。

| 命令                                 | 作用                   | 额外                               |
|------------------------------------|----------------------|----------------------------------|
| `/set_user_cold`                   | 设置用户冷却时间             | 时间内不能发送         1 为无限制           |
| `/set_group_cold`                  | 设置群组冷却时间             | 时间内不能发送            1 为无限制        |
| `/set_token_limit`                 | 设置输出限制长度             | Api 的 4095 限制是输入+输出，如果超限，那么请调小输出 |
| `/set_input_limit`                 | 设置输入限制长度             |                                  |
| `/config`                          | 获取/备份 config.json 文件 | 发送文件                             |
| `/add_block_group`      +id 绝对值    | 禁止                   | 直接生效         可跟多参数，空格分割          |
| `/del_block_group`       +id 绝对值   | 解禁                   | 直接生效          可跟多参数，空格分割         |
| `/add_block_user`     +id 绝对值      | 禁止                   | 直接生效           可跟多参数，空格分割        |
| `/del_block_user`     +id 绝对值      | 解禁                   | 直接生效           可跟多参数，空格分割        |
| `/add_white_group`     +id 绝对值     | 加入                   | 需要开启白名单模式生效       可跟多参数，空格分割     |
| `/add_white_user`      +id 绝对值     | 加入                   | 需要开启白名单模式生效       可跟多参数，空格分割     |
| `/del_white_group`     +id 绝对值     | 除名                   | 需要开启白名单模式生效        可跟多参数，空格分割    |
| `/del_white_user`      +id 绝对值     | 除名                   | 需要开启白名单模式生效      可跟多参数，空格分割      |
| `/update_detect`                   | 更新敏感词                |                                  |
| `/open_user_white_mode`            | 开用户白名单               |                                  |
| `/open_group_white_mode`           | 开群组白名单               |                                  |
| `/close_user_white_mode`           | 关用户白名单               |                                  |
| `/close_group_white_mode`          | 关群组白名单               |                                  |
| `/open`                            | 开启机器人                |                                  |
| `/close`                           | 关闭机器人                |                                  |
| `/chat`                            | 对话                   | 每次/chat 发起对话，私聊则永久。              |
| `/write`                           | 续写                   | 续写。                              |
| `/see_api_key`                     | 现在几个 Api key         |                                  |
| `/remind`                          | 人设                   | 固定的提示词。                          |
| `/del_api_key`       +key          | 删除 Api key           | 可跟多参数，空格分割                       |
| `/add_api_key`           +key      | 增加 Api key           | 可跟多参数，空格分割                       |
| `/set_per_user_limit`              | 用户分配总额度              | 1 为无限制            按用户计量          |
| `/set_per_hour_limit`              | 用户小时可用量              | 1 为无限制              按用户计量        |
| `/reset_user_usage`+userID         | 重置用户分配额度             | 按用户计量          可跟多参数，空格分割        |
| `/promote_user_limit`+userID+limit | 提升用户的额度              | 按用户计量  1 为默认        可跟多参数，空格分割   |
| `/disable_change_head`             | 禁止设定头                | 再次设定会重置为空                        |
| `/enable_change_head`              | 允许设定头                |                                  |
| `/forgetme`                        | 忘记我                  |                                  |

### 样表

```markdown
chat - 交谈
write - 续写
forgetme - 重置记忆
remind - 场景设定
set_user_cold - 设置用户冷却时间
set_group_cold - 设置群组冷却时间
set_token_limit - 设置输出限制长度
set_input_limit - 设置输入限制长度
see_api_key - 现在几个 Api key
del_api_key - 删除 Api key
add_api_key - 增加 Api key
config - 获取/备份热配置文件
set_per_user_limit - 设置普通用户额度
set_per_hour_limit - 设置用户小时额度
promote_user_limit - 提升用户额度
reset_user_usage - 重置用户额度
add_block_group - 禁止群组
del_block_group - 解禁群组
add_block_user - 禁止用户
del_block_user - 解禁用户
add_white_group - 加入白名单群组
add_white_user - 加入白名单用户
del_white_group - 除名白名单群
del_white_user - 除名白名单人
update_detect - 更新敏感词
open_user_white_mode - 开用户白名单
open_group_white_mode - 开群组白名单
close_user_white_mode - 关用户白名单
close_group_white_mode - 关群组白名单
open - 开启机器人
close - 关闭机器人
disable_change_head - 允许设定头
enable_change_head - 禁止设定头
help - 帮助
```

## 其他

### 中间件

在记忆池和分析 之间有一个 中间件，可以提供一定的联网检索支持和操作支持。可以对接其他 Api 的服务进行加料。

**Prompt Injection**

使用 `“”` `[]` 来强调内容。触发方式有正式提问的问句，介绍，询问，查询请求，小于 80 字等要求。
触发是隐式的，短的正式问句会触发。

### 统计

``analysis.json`` 是频率统计，60s 内的请求次数。

还有 total usage ，这个不包含所有用量数据，只是从 redis 拉取下来了而已

### Config.json

会自动合并缺失的键值进行修复。

### 默认参数

- 群组回复记忆为 48 hours
- 用量限制为 15000/h
- 人设记忆力为永久，追溯记忆是 80

### prompt_server.py

外设的 Prompt 裁剪接口，给其他项目提供支持。

### QuickDev

Quick Dev by MVC 框架 https://github.com/TelechaBot/BaseBot

### API
请参阅 https://github.com/sudoskys/Openaibot/blob/main/API.md 查看开放API文档。

### 上一次的性能分析

**日常负载 316MB**

## 感谢

- 贡献者
- [文本分析工具库](https://github.com/murray-z/text_analysis_tools)
- [MoeGoe Voice](https://github.com/CjangCjengh/MoeGoe)

#### 声明

```markdown
1. 此项目不是 Openai 的官方项目。
2. 不对机器人生成的任何内容负责。
```

