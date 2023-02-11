FROM python:3.10-slim AS builder
RUN apt update && apt install build-essential -y
COPY ./requirements.txt .
RUN pip install --upgrade --no-cache-dir pip && pip install --no-cache-dir -r requirements.txt
FROM python:3.10-slim
ENV WORKDIR /app
WORKDIR $WORKDIR
ADD . $WORKDIR
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
