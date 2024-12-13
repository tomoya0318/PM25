FROM python:3.12.1

WORKDIR /work

COPY requirements.txt /work/
COPY dist /work/dist

RUN apt-get update &&\
    apt-get -y install locales &&\
    localedef -f UTF-8 -i ja_JP ja_JP.UTF-8
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8
ENV TZ JST-9
ENV TERM xterm

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

COPY . /work/