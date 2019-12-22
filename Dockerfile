FROM python:3.8

ADD requirements.txt requirements.txt

RUN pip install -r requirements.txt

ADD . /home

WORKDIR /home

ENTRYPOINT ["python", "app.py", "-l"]
