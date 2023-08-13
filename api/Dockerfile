FROM ubuntu:20.04

# set the working directory
WORKDIR app

# Ensure apt is in non-interactive to avoid prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies.
RUN apt-get -y update --no-install-recommends \
    && apt-get -y install --no-install-recommends \
    python3 \
    python3-pip \
    build-essential \
    curl \
    ca-certificates \
    apt-utils \
    git \
    vim \
    libxrender1 \
    libsm6 \
    libxext6 \
    && apt-get autoremove -y \
    && apt-get clean -y

RUN PYTHONIOENCODING="utf-8" # Setup the encoding

# install dependencies
RUN pip3 install --upgrade pip
COPY ./requirements.txt .
RUN pip3 install -r requirements.txt

RUN PYTHONIOENCODING="utf-8" # Setup the encoding

# copy project
# COPY . .
