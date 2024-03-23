FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt && rm requirements.txt
RUN apt-get update && apt-get install abiword -y && apt-get install -y ca-certificates

COPY /BASED /app/turlalead

CMD ["python", "-m", "turlalead.app"]
