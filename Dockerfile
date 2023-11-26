# 第一个阶段
FROM python:3.9-buster as builder

RUN apt update && \
    apt install -y build-essential && \
    pip install -U pip setuptools wheel && \
    pip install pdm

COPY pyproject.toml pdm.lock README.md /project/
WORKDIR /project
RUN mkdir __pypackages__ && pdm sync -G bot --prod --no-editable

# 第二个阶段
FROM python:3.9-slim-buster as runtime

RUN apt update && \
    apt install -y npm && \
    npm install pm2 -g && \
    apt install -y ffmpeg

VOLUME ["/redis", "/rabbitmq", "/mongodb", "/run.log", "/config_dir"]

# retrieve packages from build stage
ENV PATH="/bin:$PATH"
ENV PYTHONPATH="/project/pkgs:$PYTHONPATH"
COPY --from=builder /project/__pypackages__/3.9/lib /project/pkgs
# retrieve executables
COPY --from=builder /project/__pypackages__/3.9/bin/* /bin/


WORKDIR /app
COPY pm2.json ./
COPY config_dir ./config_dir
COPY . /app

CMD [ "pm2-runtime", "pm2.json" ]
