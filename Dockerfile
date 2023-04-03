# pull official base image
FROM python:3.10.6-slim 

# create directory for the app user
RUN mkdir -p /home

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 0

# create the appropriate directories
ENV HOME=/home
ENV APP_HOME=/home/web
RUN mkdir $APP_HOME
WORKDIR $APP_HOME

# install psycopg2 dependencies
RUN apt-get update \
    && apt-get install -y libpq-dev gcc libpangocairo-1.0-0 netcat gettext fonts-deva

RUN pip install --upgrade pip
COPY requirements .

RUN pip install -r development.txt

# copy entrypoint.sh
COPY ./entrypoint.sh .

# copy project
COPY . .
