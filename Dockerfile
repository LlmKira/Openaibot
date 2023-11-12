# 第一个阶段
FROM python:3.11-buster as builder

RUN apt update && apt install -y build-essential \
    && pip install poetry==1.6.1

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY poetry.lock pyproject.toml ./
VOLUME ["/redis", "/rabbitmq", "/mongodb", "run.log", "/config_dir"]

RUN poetry config virtualenvs.in-project true && \
    poetry install --no-root && rm -rf $POETRY_CACHE_DIR

# 第二个阶段
FROM python:3.11-slim-buster as runtime

RUN apt update &&  \
    apt install -y npm &&  \
    npm install pm2 -g && \
    pip install poetry==1.6.1

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY pm2.json ./
COPY config_dir ./config_dir

CMD [ "pm2-runtime", "pm2.json" ]