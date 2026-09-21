FROM python:3.14-alpine@sha256:016508ba505da24f7139765bc4bb669df4e88eb2f12eeadd571bf2f88d7533df AS build

COPY Pipfile .
COPY Pipfile.lock .

# generate the requirements file
RUN python3 -m pip install pipenv && \
    pipenv requirements > requirements.txt

FROM python:3.14-alpine@sha256:016508ba505da24f7139765bc4bb669df4e88eb2f12eeadd571bf2f88d7533df AS base

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
