FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get upgrade -y && apt install -y \
    redis-server \
    python3 \
    python3-pip 

WORKDIR app
COPY . .

# Install python dependencies
RUN pip3 install -r requirements.txt

RUN PYTHONIOENCODING="utf-8" # Setup the encoding

# Add user `ubuntu`
RUN useradd -u 1000 -U -G 0 ubuntu
USER ubuntu

# Start the server
ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]

EXPOSE 5000