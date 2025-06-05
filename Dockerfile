FROM python:3.9-slim-buster

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1-mesa-glx \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

ENV PYTHONPATH "${PYTHONPATH}:/app"
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]