FROM python:3.10

RUN apt-get update && apt-get install -y python3-dev && rm -rf /var/lib/apt/lists/*

COPY . /server/application

RUN pip install -r /server/application/requirements.txt

WORKDIR /server

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "application.routes:app"]