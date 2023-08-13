FROM python:3.11.2-slim-buster

# set the working directory
WORKDIR app

# set the environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip3 install --upgrade pip
COPY ./requirements.txt .
RUN pip3 install -r requirements.txt

RUN PYTHONIOENCODING="utf-8" # Setup the encoding

# copy project
# COPY . .
