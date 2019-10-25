FROM python:3.6.9-stretch

RUN mkdir /code/
RUN mkdir /livebot/
WORKDIR /code/

ADD requirements.txt /requirements.txt
RUN python -m pip install -r /requirements.txt

ADD . /code/

CMD ["python", "bot.py"]
