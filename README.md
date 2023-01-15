![cover](https://raw.githubusercontent.com/sudoskys/Openaibot/main/docs/cover.png)


------------------------------------

<p align="center">
  <img alt="License" src="https://img.shields.io/badge/LICENSE-Other-ff69b4">
  <img src="https://img.shields.io/badge/Python-3.7|8|9|10-green" alt="PYTHON" >
  <a href="https://afdian.net/a/Suki1077"><img src="https://img.shields.io/badge/Buyme-milk-DB94A2" alt="SPONSOR"></a>
  <a href="https://app.fossa.com/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot?ref=badge_small" alt="FOSSA Status"><img src="https://app.fossa.com/api/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot.svg?type=small"/></a>
</p>


<h2 align="center">OpenaiBot</h2>

OpenAI Chat Bot For IM. 在 IM 上使用 OpenAi 交互。

如果没有您的即时通信平台或您想开发新应用体，欢迎您贡献本仓库，您可以通过调度通用事件层开发一个新的 Controller。

[EN_README](https://github.com/sudoskys/Openaibot/blob/main/README.EN.md)

本项目利用 `Api` 认证 `Token` + 上下文记忆池来实现聊天 ，并不是 `chatGPT` 的逆向，类 chatGPT 的 **Python 实现** 是自实现。

```
采用 GPT3 + 注入的方式尽量靠近ChatGpt，采用可扩展架构，等到 ChatGPT 商业化后会即时切进新的 Api，
* 靠近 chatGPT，目前 chatGPT 并未开放接口，基本全换成达芬奇了。
* 依赖库由官方的同步切换为自维护异步库。
* 逆向没有出路，我们的优势是走在尝试的最前列，提供成熟的交互体验。
* 此仓库欢迎一切贡献者。
```

[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot.svg?type=large)](https://app.fossa.com/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot?ref=badge_large)

*有问题请更新，然后提交 Issue*

## 特性

* 续写 (write)  独立推测，续写
* 聊天 (chat)  记忆桶机制，权重关联分配，更智能的上下文
* 支持 Api
* 支持私聊
* 支持群聊
* 多主人管理
* 支持速率限制
* 支持内容过滤
* 支持用量管理
* 设定固定头人设
* 支持白名单系统
* 支持黑名单系统
* 自定义风格化对话
* 多平台，泛用性强
* 完善的内容安全功能
* 多平台支持的通用接口
* 支持主动回复(For Fun)
* 动态裁剪上下文，防止超额
* 多 Api key 负载，便捷管理，超额弹出
* 插件化，实时内容支持， Prompt Injection，对Chat更友好
* chatGpt 替换为自己写的 chatGpt Openai api Python 实现
* 官方依赖库不支持异步，大量请求会阻塞，替换为自己写的异步库(最近官方才支持了异步)

## 用法

**聊天**

🔭利用 `/chat + 句子` 发起对话，然后**只需要回复**可交谈。私聊消息 或 群组 48 小时内的消息，会自动使用上下文进行推测和裁剪，直接回复就可以继续对话。

**重置**

每次使用`/forgetme` 都会重置 Ai 的记忆桶。

**续写**

🥖使用 `/write` 进行没有上下文推测的续写。

**Head**

支持场景设置，采用 `/remind` 设计自己的请求头。例如 `Ai 扮演在空间站的宇航员`。设定小于 4 个字符会使用默认值。

**Style**

支持场景设置，采用 `/style` 设计自己的风格，Ai
会倾向使用语料中的词汇，语法是 `(enhance),((enhance pro)),[[weak]],{enhance}，(中文逗号也可以)`

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
systemctl start redis.service
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

多平台。

```toml
# 不想启动哪个就注释掉那一部分

# QQ
[Controller.QQ]
master = [114, 514] # master user id , 管理者账号 ID
account = 0
http_host = 'http://localhost:8080'   # Mirai http服务器
ws_host = 'http://localhost:8080'   # Mirai Websocket服务器
verify_key = ""
trigger = false # 合适的时候主动回复
INTRO = "POWER BY OPENAI"  # 后缀
ABOUT = "Created by github.com/sudoskys/Openaibot" # 关于命令返回
WHITE = "Group NOT in WHITE list" # 黑白名单提示

# Telegram
[Controller.Telegram]
master = [114, 514] # master user id , 管理者账号 ID
botToken = '' # 机器人密钥
trigger = false # 合适的时候主动回复
INTRO = "POWER BY OPENAI"  # 后缀
ABOUT = "Created by github.com/sudoskys/Openaibot" # 关于命令返回
WHITE = "Group NOT in WHITE list" # 黑白名单提示

[Controller.BaseServer]
port = 9559
# 提供基础Api接口供Web使用
```

### 配置 Telegram 设置

[Telegram botToken 申请](https://t.me/BotFather)

然后关闭隐私模式或者提拔机器人为管理员后才能使用。

### 配置 QQ 机器人

[配置机器人后端](https://graiax.cn/before/install_mirai.html)

### 配置 Openai Api key

`Config/api_keys.json` Api Key

```json
{
  "OPENAI_API_KEY": [
    "sk-***********",
    "sk-***********"
  ]
}
```

建议在机器人私聊中配置 key

```markdown
see_api_key - 现在几个 Api key
del_api_key - 删除 Api key
add_api_key - 增加 Api key
```

[OPENAI_API_KEY 申请](https://beta.openai.com/account/api-keys)，支持多 key 分发负载。
[定价参考](https://openai.com/api/pricing/)。

请不要向任何人暴露你的 `Config`

### 配置 `service.json`

在 `Config/service.json` 下面。如果没有此文件，会使用默认值补全。

**实例**

```json
{
  "redis": {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "password": null
  },
  "proxy": {
    "status": false,
    "url": "localhost:7890"
  },
  "plugin": {
    "details": "",
    "time": "",
    "week": ""
  },
  "moderation_type": [
    "self-harm",
    "hate",
    "sexual",
    "hate/threatening",
    "sexual/minors",
    "violence",
    "violence/graphic"
  ],
  "tts": {
    "status": true,
    "type": "none",
    "vits": {
      "api": "http://127.0.0.1:9557/tts/generate",
      "limit": 70,
      "model_name": "some.pth",
      "speaker_id": 0
    },
    "azure": {
      "key": [
        ""
      ],
      "limit": 70,
      "speaker": {
        "chinese": "zh-CN-XiaoxiaoNeural"
      },
      "location": "japanwest"
    }
  }
}
```

#### Redis

```json
{
  "host": "localhost",
  "port": 6379,
  "db": 0,
  "password": null
}
```

#### 插件

```json
{
  "plugin": {
    "search": [
      "https://www.exp.com/search?word={}"
    ]
  }
}
```

`search` 就是我们自带的一个搜索插件，引擎都是要自己填写的。

放入 `plugin` 字段的插件才会被启用。
**部分插件**

| plugins   | desc              | value/server                                          | use                                   |
|-----------|-------------------|-------------------------------------------------------|---------------------------------------|
| `time`    | now time          | `""`,no need                                          | `明昨今天`....                            |
| `week`    | week time         | `""`,no need                                          | `周几` .....                            |
| `search`  | Web Search        | `["some.com?searchword={}"]`,must need                | `查询` `你知道` len<80 / end with`?`len<15 |
| `duckgo`  | Web Search        | `""`,no need,but need `pip install duckduckgo_search` | `查询` `你知道` len<80 / end with`?`len<15 |
| `details` | answer with steps | `""`,no need                                          | Ask for help `how to`                 |

[所有插件](https://github.com/sudoskys/openai-kira#plugin)

#### TTS

```shell
apt-get install ffmpeg
```

- status 开关
- type 类型

Azure/Vits 语言类型代码均为二位大写缩写字母。

**Azure 支持说明**

[具体说明](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/speech-services/)

- azure:limit 长度内的文本会被转换
- azure:speaker
  说话人, [所有声音引擎列表](https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/language-support?tabs=stt-tts)
- auzre:location 服务器资源地址
- auzre:key api key

**VITS 语音支持说明**

Api 后端请使用我打包改造的 MoeGoe https://github.com/sudoskys/MoeGoe 本机运行

- vits:limit 长度内的文本才会被转换
- vits:model_name 模型名字，some.pth,在 model 文件夹下的
- vits:speaker_id 说话人的ID,具体看模型config

安装依赖，运行 `server.py` 文件可以默认使用。
模型下载请自行寻找，并注意模型相应的协议。 如果不生效，可能是文本的长度超过了设定的 limit(`len()`) 。

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
| `/change_head`                     | 设定头                  | 用户再次设定会重置为空                      |
| `/change_style`                    | 设定头                  | 用户再次设定会重置为空                      |
| `/forgetme`                        | 忘记我                  |                                  |
| `/voice`                           | VITS/AZURE  TTS      |                                  |
| `/trigger`                         | 主动回复模式               | 全局设置或/只有管理组成员可以启动本群模式            |
| `/style`                           | 风格化指定                | 全局设置或/用户设置                       |
| `/auto_adjust`                     | 自动优化                 | owner                            |

### 样表

```markdown
chat - 交谈
write - 续写
forgetme - 重置记忆
remind - 场景设定 取消用短文本覆盖
voice - 语音支持
trigger - 管理员启动主动回复
style - 设定偏好词
auto_adjust - 自动优化器
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
change_head - 设定人设开关
change_style - 设定风格开关
help - 帮助
```

## API

请参阅 https://github.com/sudoskys/Openaibot/blob/main/docs/API.md 查看开放API文档。
API服务器与Telegram Bot服务开发进度不一，通常为Telegram
Bot出现新commit后API服务器随后适配。当某些导入模块发生变动时，API服务器可能无法正常运行。此情况下，您可切换至apiserver分支获取稳定版API服务器。

## 中间件开发

在记忆池和分析 之间有一个 中间件，可以提供一定的联网检索支持和操作支持。可以对接其他 Api 的服务进行加料。

https://github.com/sudoskys/openai-kira#plugin-dev

## 其他

### 多 Controller 域指数

| Controller | suffix_id | desc |
|------------|-----------|------|
| QQ         | 101       |      |
| Telegram   | 100       |      |
| Api        | 103       |      |

### 统计 `analysis.json`

如果没有请新建填充`{}`

此文件为频率统计，为 60s 内的请求次数。

用户在使用时， `total usage`会被更新到此文件。如果你要备份用量数据，请备份 Redis 数据库。

### 配置文件 `Config.json`

需要经常使用命令备份。如果没有请新建填充`{}`或删除，会自动合并缺失的键值进行修复。

### 默认参数

- 群组回复记忆为 48 hours
- 用量限制为 15000/h
- 人设记忆力为永久，追溯记忆是 80

### prompt_server.py

外设的 Prompt 裁剪接口，给其他项目提供支持。

### QuickDev

Quick Dev by MVC 框架 https://github.com/TelechaBot/BaseBot

### 上一次的性能分析

**日常负载内存 316MB**

## 感谢

- 贡献者
- [文本分析工具库](https://github.com/murray-z/text_analysis_tools)
- [MoeGoe Voice](https://github.com/CjangCjengh/MoeGoe)

## CLAUSE

CLAUSE 说明了如何授权，声明，附加条款等内容。

![CLAUSE](https://github.com/sudoskys/Openaibot/main/CLAUSE.md)
