## 解决依赖问题

apt-get install python3-pyaudio

然后软连接系统的C库 来解决 C库问题。

```bash
ln -sf /usr/lib/libstdc++.so.6 /home/someone/miniconda3/envs/OpenAi/lib/libstdc++.so.6
```

## 解决录音问题

没解决。