FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt && rm requirements.txt

COPY /BASED /app/BASED

CMD ["python", "-m", "BASED.app"]
