FROM python:3.9.16-slim

COPY . /app

WORKDIR /app
RUN pip3 install -r requirements.txt

CMD ["python3", "/app/alert.py"]