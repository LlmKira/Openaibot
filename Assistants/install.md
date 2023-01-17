# 配置细则

client 除了唤醒都可以依赖网络来解决，但是 BaseServer 我没有做鉴权，所以大概适合局域网使用。

## 解决依赖问题

apt-get install python3-pyaudio

然后软连接系统的 C库 来解决 C库 问题。

```bash
ln -sf /usr/lib/libstdc++.so.6 /home/someone/miniconda3/envs/OpenAi/lib/libstdc++.so.6
```

## 配置

`Config/assistants.json`

```json
{
  "rec": {
    "porcupine": {
      "key": "Bh=="
    }
  },
  "userid": 10086,
  "sst": {
    "select": "whisper",
    "lang": "zh",
    "whisper": {},
    "azure": {
      "key": [
        ""
      ],
      "lang": {
        "zh": "zh-CN"
      },
      "location": "japanwest"
    }
  },
  "sound": {
    "save": true,
    "dir": "sound"
  },
  "chat": {
    "gpt_server": "http://127.0.0.1:9559"
  },
  "prompt": {
    "start_sequ": "Human",
    "restart_sequ": "Neko",
    "role": "",
    "character": [
      "string"
    ],
    "head": "",
    "model": "text-davinci-003"
  }
}
```

## 如果不能用麦克风

`sudo pacman -S pipewire pipewire-pulse pipewire-alsa`

`systemctl --user start pipewire pipewire-pulse pipewire-media-session`

重启

`yay -S helvum`

打开 `helvum` ，运行程序，把麦克风(mic)连到 Python。

## 注册 porcupine

[关键词唤醒服务](https://console.picovoice.ai/)

## 使用

运行 `client.py`

说 `Hi Coco` + 文本

## 设计架构

在输入方面采用回调函数注册机制。返回录音识别的内容。

```
    Api 传入层|Api工具层                     
触发|wav输入层|识别层|Base Server|TTS 层提取|返回层|
                                        |API 返回层

```