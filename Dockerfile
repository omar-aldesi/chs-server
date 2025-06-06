# chs_backend/Dockerfile
FROM python:3.10-slim-buster

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Alembic files
COPY alembic/ alembic/
COPY alembic.ini .

# Copy the entire app directory structure
COPY app/ app/
# Copy any other necessary files
COPY . .

# Ensure the working directory is correct
WORKDIR /app

# Set Python path to include the current directory
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]