FROM python:3.7-alpine

# env vars
ENV ENV_CONFIGURATION=True \
    FEEDS_PATH=/feedforbot/feeds.yml

# add files and user
RUN adduser -D -h /feedforbot feedforbot
WORKDIR /feedforbot

# setup requirements
ADD requirements.txt requirements.txt
RUN pip install --disable-pip-version-check --requirement requirements.txt

# execute from user
USER feedforbot
ADD ./src .

ENTRYPOINT ["python", "app.py"]
