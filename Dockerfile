# Use official Python runtime as base image
FROM python:3.11-slim

# Set working directory in container
WORKDIR /app

# Copy project files
COPY . /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (if needed for any services)
EXPOSE 8000

# Set default command
ENV PYTHONPATH=/app
CMD ["python", "Interface.py"]
