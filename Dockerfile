FROM python:bullseye

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=true

RUN apt-get update && \
    apt-get install -y git && \
    apt-get install -y python3-pip && \
    apt-get clean

RUN groupadd -g 1100 gitsync
RUN useradd -m -u 1100 -g 1100 gitsync

RUN mkdir -pv /var/opt/gitsync
RUN chown -R 1100:1100 /var/opt/gitsync

COPY --chown=1100:1100 . /var/opt/gitsync

WORKDIR /var/opt/gitsync

VOLUME [ "/home/gitsync/.ssh", "/var/opt/gitsync/config" ]

RUN python -m pip install -r requirements.txt

USER gitsync

CMD [ "/usr/bin/env", "python3", "gitsync.py" ]