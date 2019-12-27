FROM python:3.7-alpine

# env vars
ENV FEEDS_PATH='feeds.yml'

# add files anf user
RUN adduser -D -h /home/feedforwarder feedforwarder
WORKDIR /home/feedforwarder

# setup requirements
ADD requirements.txt requirements.txt
RUN pip install --disable-pip-version-check --requirement requirements.txt

# execute from user
USER feedforwarder

ADD ./src .

ENTRYPOINT ["python", "app.py"]
