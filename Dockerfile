FROM python:3.10-slim AS builder

RUN apt update &&  \
    apt install build-essential -y
RUN apt-get update &&  \
    apt install -y npm &&  \
    npm install pm2 -g

COPY ./requirements.txt .
COPY pm2.json .
COPY settings.toml .
COPY start.sh .

VOLUME ["/redis", "/rabbitmq", "/mongodb", "run.log"]

RUN pip install --upgrade --no-cache-dir pip && pip install --no-cache-dir -r requirements.txt



FROM python:3.10-slim
ENV WORKDIR /app
WORKDIR $WORKDIR
ADD . $WORKDIR
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
ENTRYPOINT [ "sh", "./start.sh" ]