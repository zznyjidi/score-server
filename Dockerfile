FROM python:3.13

ADD requirements.txt /
RUN pip install -r /requirements.txt

RUN mkdir /app
ADD src/ /app

WORKDIR /app

EXPOSE 8080
CMD [ "python", "app.py" ]
