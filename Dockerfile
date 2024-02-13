FROM python:3

WORKDIR /app

COPY blockchain/ .

RUN pip install Flask boto3 requests matching python-dateutil

EXPOSE 5000

CMD ["python", "main.py", "--host=0.0.0.0"]