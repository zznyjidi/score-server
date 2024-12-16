FROM python:latest

ADD requirements.txt /
RUN pip install -r /requirements.txt

RUN mkdir /app
ADD server/ /app

WORKDIR /app

EXPOSE 8080
CMD [ "python", "server.py" ]
