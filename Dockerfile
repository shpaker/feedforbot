FROM python:onbuild

MAINTAINER shpaker <shpaker@gmail.com>

# copy our application code
# ADD FeedsBot /opt/feedsbot
# WORKDIR /opt/feedsbot

ENTRYPOINT ["python", "app.py"]
