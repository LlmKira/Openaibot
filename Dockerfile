FROM python:3.11-buster as builder

RUN apt update &&  \
    apt install build-essential -y &&  \
    pip install poetry==1.6.1

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./
VOLUME ["/redis", "/rabbitmq", "/mongodb", "run.log", "/config_dir"]

RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

FROM python:3.11-slim-buster as runtime

RUN apt-get update &&  \
    apt install -y npm &&  \
    npm install pm2 -g \

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

ENV WORKDIR /app
WORKDIR $WORKDIR
ADD . $WORKDIR

COPY pm2.json ./
# 将 config_dir 的设置文件复制到 /config_dir
COPY config_dir ./config_dir

CMD [ "pm2-runtime", "pm2.json" ]