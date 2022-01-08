FROM python:3.9-alpine
ENV PYTHONUNBUFFERED 1

ADD deploiements/requirements.txt /requirements.txt

RUN apk update \
    && apk --no-cache upgrade \
    && apk add --no-cache --virtual .build-deps \
    ca-certificates gcc linux-headers musl-dev libffi-dev

RUN pip install --upgrade pip \
    && pip install -r /requirements.txt

COPY . /home
WORKDIR /home

RUN chmod +x /home/SerreConnectee/entrypoint.sh

EXPOSE 6023

ENTRYPOINT ["/home/SerreConnectee/entrypoint.sh"]