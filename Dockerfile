FROM python:alpine

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

RUN python -m pip install -r requirements.txt

USER gitsync

CMD [ "/usr/bin/env", "python3", "gitsync.py" ]