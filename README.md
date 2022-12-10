# Openaibot

OpenAI Chat Telegram Bot

[EN_README](https://github.com/sudoskys/Openaibot/blob/main/README.EN.md)

在 Telegram 上使用 OpenAi 交互. Python > 3.7。

本程序利用 `Api` 认证 `Token` 运作，并不是 `chatGPT` 的逆向，chatGPT **功能**的 **Python 实现** 由本机器人自实现。

```
This is not an official OpenAI product. This is a personal project and is not affiliated with OpenAI in any way. Don't sue me
```

**不对机器人生成的任何内容负责，内容由OpenAi提供**

*自己实现的 chatGPT ，体验基本一样，就是 Api 要钱*

*自制异步依赖库*

## 特性

* 聊天(chat) chatGpt 自实现 + NLP增强
* 续写(write)  独立推测，续写
* 设定固定头人设
* 多主人管理
* 多Api key 负载，超额弹出。
* chatGPT api 版本实现，不逆向 preview 的 api
* 支持私聊
* 支持群聊
* 支持速率限制
* 支持用量管理
* 支持白名单系统
* 支持黑名单系统
* 支持内容过滤
* (20221205) 依赖库不支持异步，大量请求会阻塞,替换为自己写的异步库
* chatGpt 替换为自己写的 chatGpt Openai api Python 实现
* 动态裁剪上下文

见 https://github.com/sudoskys/Openaibot/issues/1

**聊天**

🔭利用 `/chat + 句子` 可重置 AI 的记忆，然后只需要`回复`即可交谈。私聊消息 或 群组24小时内的消息，会自动使用上下文进行推测和裁剪，直接回复就可以继续对话。

每次使用`/chat` 都会重置 Ai 的记忆桶。

/write +句子 进行续写

**续写**

🥖使用 `/write` 进行没有上下文推测的续写。

**Head**

支持人设设置，采用 `/remind` 设计自己的请求头。

## 初始化

服务器内存大于 500MB ，因为用到了 NLP 技术支持上下文。

* 拉取/更新程序

安装脚本会自动备份恢复配置，在根目录运行(不要在程序目录内)
，更新时候重新运行就可以备份程序了，如果是小更新可以直接 ``git pull``

```shell
curl -LO https://raw.githubusercontent.com/sudoskys/Openaibot/main/setup.sh && sh setup.sh
```

`cd Openaibot`

## 配置

### 配置 Redis

**本机**

```shell
apt-get install redis
```

**Docker + 持久化（保存在 ./redis 目录下）**

```
docker run --name redis -d -v $(pwd)/redis:/data -p 6379:6379 redis redis-server --save 60 1 --loglevel warning
```

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
master = [100, 200] # master user id &owner
botToken = 'key'
INTRO = "POWER BY OPENAI"  # 后缀
ABOUT = "Created by github.com/sudoskys/Openaibot"
WHITE = "Group NOT in WHITE list"

[proxy]
status = false
url = "http://127.0.0.1:7890"
```

[Telegram botToken 申请](https://t.me/BotFather)

**配置 key**

```markdown
see_api_key - 现在几个 Api key
del_api_key - 删除 Api key
add_api_key - 增加 Api key
```

[OPENAI_API_KEY 申请](https://beta.openai.com/account/api-keys)，支持多 key 分发负载
[定价参考](https://openai.com/api/pricing/)

请不要向任何人暴露你的 `app.toml`

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

限制类设置设定为 `1` 代表不生效。

| 命令                                 | 作用                   | 额外                                         |
|------------------------------------|----------------------|--------------------------------------------|
| `/set_user_cold`                   | 设置用户冷却时间             | 时间内不能发送         1 为无限制                     |
| `/set_group_cold`                  | 设置群组冷却时间             | 时间内不能发送            1 为无限制                  |
| `/set_token_limit`                 | 设置输出限制长度             | Api的4095限制是输入+输出，如果超限，那么请调小输出              |
| `/set_input_limit`                 | 设置输入限制长度             |                                            |
| `/config`                          | 获取/备份 config.json 文件 | 发送文件                                       |
| `/add_block_group`      +id绝对值     | 禁止                   | 直接生效         可跟多参数，空格分割                    |
| `/del_block_group`       +id绝对值    | 解禁                   | 直接生效          可跟多参数，空格分割                   |
| `/add_block_user`     +id绝对值       | 禁止                   | 直接生效           可跟多参数，空格分割                  |
| `/del_block_user`     +id绝对值       | 解禁                   | 直接生效           可跟多参数，空格分割                  |
| `/add_white_group`     +id绝对值      | 加入                   | 需要开启白名单模式生效       可跟多参数，空格分割               |
| `/add_white_user`      +id绝对值      | 加入                   | 需要开启白名单模式生效       可跟多参数，空格分割               |
| `/del_white_group`     +id绝对值      | 除名                   | 需要开启白名单模式生效        可跟多参数，空格分割              |
| `/del_white_user`      +id绝对值      | 除名                   | 需要开启白名单模式生效      可跟多参数，空格分割                |
| `/update_detect`                   | 更新敏感词                |                                            |
| `/open_user_white_mode`            | 开用户白名单               |                                            |
| `/open_group_white_mode`           | 开群组白名单               |                                            |
| `/close_user_white_mode`           | 关用户白名单               |                                            |
| `/close_group_white_mode`          | 关群组白名单               |                                            |
| `/open`                            | 开启机器人                |                                            |
| `/close`                           | 关闭机器人                |                                            |
| `/chat`                            | 对话                   | 每次/chat都会重新开始，遗忘记录。群组中 24 h 后不能索引回复，私聊则永久。 |
| `/write`                           | 续写                   | 续写.                                        |
| `/see_api_key`                     | 现在几个 Api key         |                                            |
| `/remind`                          | 人设                   | 固定的提示词.                                    |
| `/del_api_key`       +key          | 删除 Api key           | 可跟多参数，空格分割                                 |
| `/add_api_key`           +key      | 增加 Api key           | 可跟多参数，空格分割                                 |
| `/set_per_user_limit`              | 用户分配总额度              | 1 为无限制            按用户计量                    |
| `/set_per_hour_limit`              | 用户小时可用量              | 1 为无限制              按用户计量                  |
| `/reset_user_usage`+userID         | 重置用户分配额度             | 按用户计量          可跟多参数，空格分割                  |
| `/promote_user_limit`+userID+limit | 提升用户的额度              | 按用户计量  1为默认        可跟多参数，空格分割              |

### 样表

```markdown
chat - 交谈
write - 补全
remind - 人设
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
```

## 其他

### 统计

``analysis.json`` 是频率统计，60s 内的请求次数。

还有 total usage ，这个不包含所有用量数据，只是从 redis 拉取下来了而已

### Config.json

会自动合并缺失的键值进行修复。

### 默认参数

- 群组回复记忆为 24 hours
- 用量限制为 60000/h
- 上下文记忆力为 7
- 触发截断的字符数为 3333x4 (api:max 4095x4) (tokenx4 粗略估算)

### prompt_server.py

外设的 Prompt 裁剪接口，给其他项目提供支持。

### QuickDev

Quick Dev by MVC 框架 https://github.com/TelechaBot/BaseBot

