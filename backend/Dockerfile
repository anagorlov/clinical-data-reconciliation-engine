# Dockerfile
# EHR Clinical Data Reconciliation Engine
# By: Anastasiya Gorlov
# Wed, March 18th, 2026
# This is the bonus feature for: Docker containerization
# Convenient, lets anyone run our app with one command (no need to install everything)

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
