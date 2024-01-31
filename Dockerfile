# Create the builder Backend
FROM python:3.11.6-slim AS builder
LABEL 'maintainer' 'freddy.bello@upr.edu'

WORKDIR /app

# Install poppler utility for PDF Processing and clean up
RUN apt-get update \
    && apt-get install -y poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade  -r requirements.txt

# # Create Runner
# FROM python:3.11.6-slim AS runner

# set env variables
# Prevents Python from writing pyc and from buffering stdout and stderr
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# copy project
# COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .

# Expose the port on which the api will run
EXPOSE 8000

# Run the FastAPI application using uvicorn server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]