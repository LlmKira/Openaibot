# 第一个阶段
FROM python:3.11-buster as builder

RUN apt update && \
    apt install -y build-essential && \
    pip install -U pip setuptools wheel && \
    pip install pdm

COPY pyproject.toml pdm.lock README.md /app/
COPY llmkira /app/llmkira

WORKDIR /app
RUN mkdir __pypackages__ && pdm sync -G bot --prod --no-editable

# 第二个阶段
FROM python:3.11-slim-buster as runtime

RUN apt update && \
    apt install -y npm && \
    npm install pm2 -g && \
    apt install -y ffmpeg

VOLUME ["/redis", "/rabbitmq", "/mongodb", "/run.log", "/config_dir"]

ENV PYTHONPATH=/project/pkgs
COPY --from=builder /app/__pypackages__/3.11/lib /project/pkgs
# retrieve executables
COPY --from=builder /app/__pypackages__/3.11/bin/* /bin/

WORKDIR /app
COPY pm2.json ./
COPY config_dir ./config_dir
COPY . /app

CMD [ "pm2-runtime", "pm2.json" ]
