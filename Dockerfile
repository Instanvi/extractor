# Use the official Python 3.11.7 slim image as the base
FROM python:3.11-slim

# Install system dependencies, including Tesseract and libGL
RUN apt-get update && \
    apt-get install -y tesseract-ocr libtesseract-dev libgl1 && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /extractor

# Copy the project files into the container
COPY . /extractor

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port FastAPI runs on
EXPOSE 10000

# Run the FastAPI app using Uvicorn
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "10000"]
