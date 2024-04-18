# 第一个阶段
FROM python:3.9-buster as builder

RUN apt update && \
    apt install -y build-essential && \
    pip install -U pip setuptools wheel && \
    pip install pdm && \
    apt install -y ffmpeg

COPY pyproject.toml pdm.lock README.md /project/
WORKDIR /project
RUN pdm sync -G bot --prod --no-editable

# 第二个阶段
FROM python:3.9-slim-buster as runtime

RUN apt update && \
    apt install -y npm && \
    npm install pm2 -g && \
    apt install -y ffmpeg && \
    pip install pdm

VOLUME ["/redis", "/rabbitmq", "/mongodb", "/run.log", ".cache",".montydb",".snapshot"]

WORKDIR /app
COPY --from=builder /project/.venv /app/.venv

COPY pm2.json ./
COPY . /app

CMD [ "pm2-runtime", "pm2.json" ]
