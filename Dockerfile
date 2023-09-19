FROM python:3.10-slim AS builder
RUN apt update && apt install build-essential -y

COPY ./requirements.txt .

RUN pip install --upgrade --no-cache-dir pip && pip install --no-cache-dir -r requirements.txt

#RUN apt-get install -y npm
#RUN npm install pm2 -g

COPY wait-for-it.sh /wait-for-it.sh
COPY ./start.sh .

RUN chmod +x /wait-for-it.sh

ENV WORKDIR /app
WORKDIR $WORKDIR

FROM python:3.10-slim
ADD . $WORKDIR
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

ENTRYPOINT [ "sh", "./start.sh" ]
