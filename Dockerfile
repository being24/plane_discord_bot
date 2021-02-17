FROM python:3.8-alpine

WORKDIR /opt/

ENV LC_CTYPE='C.UTF-8'
ENV TZ='Asia/Tokyo'
ENV DEBIAN_FRONTEND=noninteractive

RUN set -x && \
    apk add --no-cache build-base nano git tzdata ncdu && \
    cp /usr/share/zoneinfo/Asia/Tokyo /etc/localtime && \
    python3 -m pip install -U setuptools && \
    git clone https://github.com/being24/plane_discord_bot.git && \
    python3 -m pip install -r ./plane_discord_bot/requirements.txt && \
    python -m pip install -U git+https://github.com/Rapptz/discord-ext-menus && \
    chmod 0700 ./plane_discord_bot/*.sh && \
    chmod 0700 ./plane_discord_bot/bot.py && \
    apk del build-base  && \
    rm -rf /var/cache/apk/*  && \
    echo "Hello, plane_discord_bot ready!" 

CMD ["/opt/plane_discord_bot/bot.sh"]