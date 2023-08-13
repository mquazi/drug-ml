FROM informaticsmatters/rdkit-python3-debian:Release_2020_09
USER ${UID}:${GID}

ENV DEBIAN_FRONTEND noninteractive
RUN apt update --allow-releaseinfo-change && \
    apt upgrade -y && \
    apt install -y perl && \
    rm -rf /var/lib/apt/lists/*

# set the working directory
WORKDIR app

# install dependencies
RUN pip3 install --upgrade pip
COPY ./requirements.txt .
RUN pip3 install -r requirements.txt

RUN PYTHONIOENCODING="utf-8" # Setup the encoding

# copy project
# COPY . .
