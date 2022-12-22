FROM python:3.10-slim AS builder
ENV WORKDIR /app
WORKDIR $WORKDIR
ADD . $WORKDIR
RUN apt-get install build-essential -y
RUN pip install --upgrade --no-cache-dir pip && pip install --no-cache-dir -r requirements.txt