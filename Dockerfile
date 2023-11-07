FROM python:3.10-slim AS builder

RUN apt update &&  \
    apt install build-essential -y

COPY ./requirements.txt .
COPY pm2.json .
COPY start.sh .
# 将 config_dir 的设置文件映射到宿主机
COPY ./config_dir /config_dir

VOLUME ["/redis", "/rabbitmq", "/mongodb", "run.log", "/config_dir"]

RUN pip install --upgrade --no-cache-dir pip && pip install --no-cache-dir -r requirements.txt

FROM python:3.10-slim
RUN apt-get update &&  \
    apt install -y npm &&  \
    npm install pm2 -g

ENV WORKDIR /app
WORKDIR $WORKDIR
ADD . $WORKDIR
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
CMD [ "pm2-runtime", "pm2.json" ]