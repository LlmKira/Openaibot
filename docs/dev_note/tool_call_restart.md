## Snapshot 函数快照

因为系统通过消息队列指导发送，所以可以暂存队列消息，合适的时候再重新发送。

内置了下一个节点的函数。和层级信息等等。

````json5
{
  "task_sign": {
    "sign_as": [
      4,
      "chain",
      "llm_task",
      "2CXKW"
    ],
    "instruction": null,
    "disable_tool_action": false,
    "tool_response": [
      {
        "name": "search_in_google",
        "function_response": "Search Api:\n<doc id=0 link=https://baike.baidu.com/item/%E6%B4%9B%E5%A4%A9%E4%BE%9D/6753346 title=洛天依_百度百科> \n洛天依（Luo Tianyi），7月12日出生，是基于语音合成软件VOCALOID系列制作的女性虚拟歌手、虚拟偶像，形象由MOTH参与设计，声源是由山新、鹿乃担任，现隶属于上海禾念信息 ...\n<doc>\n<doc id=1 link=https://vocaloid.fandom.com/zh/wiki/%E6%B4%9B%E5%A4%A9%E4%BE%9D?variant=zh title=洛天依 - Vocaloid Wiki> \n基本资料 · 国籍：中国 · 性别：女 · 生日：7月12日 · 年龄：15岁 · 身高：156CM · 发色：灰色 · 瞳色：绿色 · 性格：温柔敏感 ...\n<doc>\n<doc id=2 link=https://weibo.com/5146173015/N8WjZBjmf title=洛天依11周年生日快乐##洛天依0712生日快... 来自Vsinger - 微博> \n洛天依11周年生日快乐#❀#洛天依0712生日快乐# 转发关注并点击直播预约http://t.cn/A60P2e3O，揪3位小伙伴送出【洛天依随机款式挂件】1个。\n<doc>\n<doc id=3 link=https://m.ximalaya.com/ask/q6013354 title=洛天依的生日是什么 - 喜马拉雅> \n洛天依（雅音宫羽），15岁，是以Yamaha的VOCALOID 3语音合成引擎为基础的全世界第一款中文VOCALOID声库和虚拟形象。洛天依的声库于2012年7月12日在第八届 ...\n<doc>",
        "tool_call_id": "call_vOACb300Pbt78iVUV8swMeZO",
        "tool_call": {
          "id": "call_vOACb300Pbt78iVUV8swMeZO",
          "type": "function",
          "function": {
            "name": "Search",
            "arguments": "{\"keywords\":\"洛天依生日\"}"
          }
        }
      }
    ],
    "memory_able": true,
    "router": "answer",
    "response_snapshot": true,
    "tools_ghost": [
      {
        "type": "function",
        "function": {
          "name": "Search",
          "description": "dict() -> new empty dictionary",
          "parameters": {
            "type": "object",
            "properties": {
              "keywords": {
                "title": "Keywords",
                "type": "string"
              }
            },
            "required": [
              "keywords"
            ]
          }
        }
      },
      {
        "type": "function",
        "function": {
          "name": "SetAlarm",
          "description": "dict() -> new empty dictionary",
          "parameters": {
            "type": "object",
            "properties": {
              "delay": {
                "description": "The delay time, in minutes",
                "title": "Delay",
                "type": "integer"
              },
              "content": {
                "description": "reminder content",
                "title": "Content",
                "type": "string"
              }
            },
            "required": [
              "content",
              "delay"
            ]
          }
        }
      }
    ],
    "tool_calls_counter": 0,
    "tool_calls_limit": 5,
    "tool_calls_pending": [
      {
        "id": "call_zveMoa9A5EODXK9qiUnjdr7f",
        "type": "function",
        "function": {
          "name": "SetAlarm",
          "arguments": "{\"delay\":5,\"content\":\"洛天依的生日是7月12日，她出生于这一天。\"}"
        }
      }
    ],
    "tool_calls_completed": [],
    "snapshot_credential": "LQ5RZ",
    "certify_needed_map": {
      "LQ5RZ": {
        "id": "call_zveMoa9A5EODXK9qiUnjdr7f",
        "type": "function",
        "function": {
          "name": "SetAlarm",
          "arguments": "{\"delay\":5,\"content\":\"洛天依的生日是7月12日，她出生于这一天。\"}"
        }
      }
    },
    "llm_response": {
      "id": "chatcmpl-9FJDsYE9hfdZZhMBV5WaSm80SycMa",
      "model": "gpt-3.5-turbo-0125",
      "choices": [
        {
          "index": 0,
          "message": {
            "role": "assistant",
            "content": null,
            "name": null,
            "tool_calls": [
              {
                "id": "call_zveMoa9A5EODXK9qiUnjdr7f",
                "type": "function",
                "function": {
                  "name": "SetAlarm",
                  "arguments": "{\"delay\":5,\"content\":\"洛天依的生日是7月12日，她出生于这一天。\"}"
                }
              }
            ]
          },
          "finish_reason": "tool_calls",
          "delta": null,
          "logprobs": null
        }
      ],
      "usage": {
        "prompt_tokens": 758,
        "completion_tokens": 40,
        "total_tokens": 798
      },
      "object": "chat.completion",
      "created": 1713435840,
      "system_fingerprint": "fp_1265751211"
    }
  },
  "sender": {
    "platform": "telegram",
    "user_id": "1265751211",
    "chat_id": "1265751211",
    "thread_id": null,
    "message_id": "3403"
  },
  "receiver": {
    "platform": "telegram",
    "user_id": "1265751211",
    "chat_id": "1265751211",
    "thread_id": null,
    "message_id": "3403"
  },
  "message": []
}
````

## 函数调用

当函数调用完成后，因为结束标志是 `tool_calls`，所以需要再次启动链条，达成递归动作。

这里有个问题，tool call 可能是单个或者多个的。

如果LLM把任务都拆成多个，我们需要注册大量函数快照。这样会导致十分频繁的回复，所以我们需要辨别哪些快照是不必要生成的。

但是单个任务又不能预测到下一个。所以既然如此。如果上一个动作的调用是单个的，那么我们就不生成快照。（相当于连续两个单调）。

管理这个状态非常困难，所以我们需要 **通过时间** 判断单个接受者短时间内有没有生成连续的toolcall。达成时序上的判断。
