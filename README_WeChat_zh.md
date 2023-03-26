# Openaibot 微信部署指南

## 简介

主流 ChatGPT 微信机器人使用 [wechaty](https://github.com/wechaty/wechaty)、itchat-uos 等热门解决方案实现，均需扫码登录，且已经有封号的案例。一些号码被限制无法登录网页版微信，也影响同类接口的使用体验。故本实现与微信的对接，选择了 Hook Windows 客户端的解决方案 [WeChatFerry](https://github.com/lich0821/WeChatFerry)。

### 优点：

100%原生微信；稳定可靠；**接口所有权归自己**；目前看来还没有被针对

### 缺点也是显而易见的：

微信客户端需停在指定版本，不能更新；占用登录数，机器人工作时自己无法使用电脑版微信；需要一台 Windows 环境的电脑或虚机挂微信，浪费资源。

之所以开此奇法，除以上优点之外，还有**避免重复造轮子**的考虑（主流方法已经被集成得很完善了，有很多成熟的机器人项目，没有再重新实现一遍的必要）。水平有限还望不吝赐教。

## 部署方式

WeChatFerry 的配置请见[项目主页](https://github.com/lich0821/WeChatFerry)。介绍三种可能的部署策略：

### １、Openaibot 在 Linux 或 Docker 环境部署；用本地电脑、虚拟机或另一台 Windows VPS 起微信环境。

考虑到 Win 机通常在内网，可以使用 [frp](https://github.com/fatedier/frp) 做端口映射。Openaibot 服务器开 `frps`，对外暴露一个端口接受连接；Win 端开 `frpc`，连接到服务器，将本地 `10086、10087` 端口映射到服务器，映射后的端口只对内不对外。这样对于服务器而言，就好像后端在本机开的一样，而实际上微信仍在国内。

`【具体配置文件内容待补】`

### ２、Openaibot 在 Linux 或 Docker 环境部署，并在同一台机器上起 Windows 虚机挂微信（x86 限定）

这种方案对部署主机的性能要求很高。只需跑起 32 位 Win7/8/10 即可，所以不需要主机支持虚拟化。每个虚机占用 1~1.5GB 左右 RAM 和 25GB 左右磁盘空间。建议使用[此处](https://github.com/IL01DI/Tiny10/releases)的极简 Win10；因精简的太狠，无中文字库。拷一个宋体到 `C:\Windows\Fonts` 下即可解决中文显示问题。

配好虚机后设置网卡，将虚机的 `10086、10087` 端口暴露给宿主即可。

`【具体操作步骤待补】`

### ３、所有环境都部署在 Windows 上【已测试通过】

建议在本地电脑/虚机上跑，因为此法对 VPS 的 RAM 容量、硬盘大小也有较高要求。如果 VPS 性能足够好，修改引导、重新分区、安装准虚拟化驱动后也能强制安装上 Windows。思路如下：

    1.先向安装镜像中注入磁盘驱动、网卡驱动等
    2.服务器端下一个能分区的 livecd（如 gparted livecd），修改引导，从该 livecd 启动
    3.压缩出一个 5GB 左右的 FAT32 分区
    4.解压备好的安装镜像到该分区
    5.修改引导从该分区的 bootmgr 启动
    6.格式化 Linux 分区并安装 Windows

`【具体操作步骤待补】`

Redis 是 Windows 上部署本项目的障碍，但 Win10/11 有官方支持、基于虚拟化的 Redis。微软也发布过非官方的 Redis（版本较旧，但足以支持本项目运行，原生 Windows 应用程序，支持低版本 Win: [链接](https://github.com/MicrosoftArchive/redis/releases)）。
