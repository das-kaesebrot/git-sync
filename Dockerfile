FROM python:3.14-alpine@sha256:31da4cb527055e4e3d7e9e006dffe9329f84ebea79eaca0a1f1c27ce61e40ca5 AS build

COPY Pipfile .
COPY Pipfile.lock .

# generate the requirements file
RUN python3 -m pip install pipenv && \
    pipenv requirements > requirements.txt

FROM python:3.14-alpine@sha256:31da4cb527055e4e3d7e9e006dffe9329f84ebea79eaca0a1f1c27ce61e40ca5 AS base

ENV PYTHONUNBUFFERED=true

RUN apk add --no-cache \
    openssh-client \
    git

RUN adduser -u 1100 -D gitsync

RUN mkdir -pv /var/opt/gitsync
RUN chown -R 1100:1100 /var/opt/gitsync

COPY --chown=1100:1100 . /var/opt/gitsync

WORKDIR /var/opt/gitsync

VOLUME [ "/var/opt/gitsync/config" ]

COPY --from=build requirements.txt .
RUN python -m pip install -r requirements.txt

USER gitsync

CMD [ "/usr/bin/env", "python3", "gitsync.py" ]
