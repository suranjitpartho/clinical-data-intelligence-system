# STAGE 1: Build the React Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# STAGE 2: Build the Python Backend & Serve Frontend
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all necessary project files
COPY app/ ./app
COPY scripts/ ./scripts
COPY migrations/ ./migrations
COPY alembic.ini .
COPY .env .
COPY entrypoint.sh .

# Copy the React build from Stage 1
COPY --from=frontend-builder /frontend/dist ./static/

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Expose the port
EXPOSE 8000

# Use the entrypoint script to handle migrations, seeding, and startup
ENTRYPOINT ["./entrypoint.sh"]
