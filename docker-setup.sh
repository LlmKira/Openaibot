function install() {
    # 安装docker
    if command -v dc >/dev/null 2>&1; then 
        
    else 
        curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun
    fi

    #拉取镜像
    docker pull sudoskys/openaibot:main

    #创建配置文件
    #...
}

function usage() {
  echo "Usage: "
  echo "....."
}

function main() {
  case "${action}" in
  install)
    install
    ;;
  upgrade)
    upgrade
    ;;
  start)
    start
    ;;
  restart)
    restart
    ;;
  stop)
    stop
    ;;
  pull)
    pull
    ;;
  close)
    close
    ;;
  status)
    status
    ;;
  uninstall)
    uninstall
    ;;
  config)
    config
    ;;
  help)
    usage
    ;;
  --help)
    usage
    ;;
  -h)
    usage
    ;;
  *)
    echo "No such command: ${action}"
    usage
    ;;
  esac
}

main "$@"
