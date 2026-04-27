# Use a more complete base image just in case
FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Explicitly use shell to expand $PORT
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
