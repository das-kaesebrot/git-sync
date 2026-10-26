FROM python:3.14-alpine@sha256:601e99e090cb08c2784a42395487709500bc39930307fe72f3f11a8f3c430762 AS build

COPY Pipfile .
COPY Pipfile.lock .

# generate the requirements file
RUN python3 -m pip install pipenv && \
    pipenv requirements > requirements.txt

FROM python:3.14-alpine@sha256:601e99e090cb08c2784a42395487709500bc39930307fe72f3f11a8f3c430762 AS base

ENV PYTHONUNBUFFERED=true

RUN apk add --no-cache \
    openssh-client \
    git git-lfs

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
