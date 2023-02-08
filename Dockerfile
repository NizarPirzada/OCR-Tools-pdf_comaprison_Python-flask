FROM python:3.7.7-slim-buster
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc
RUN apt-get install -y --no-install-recommends \
    gfortran \
    musl-dev \
    g++
RUN mkdir /project
# Test
WORKDIR /project
ADD . /project
RUN pip install -r requirements.txt
RUN export FLASK_APP=app.py
RUN flask db init
RUN flask db migrate
RUN flask db upgrade
EXPOSE 5050
CMD flask run