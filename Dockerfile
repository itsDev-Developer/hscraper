# Use full Python image to avoid missing packages
FROM python:3.12-bullseye

WORKDIR /app

# Install Chromium dependencies
RUN apt-get update && apt-get install -y \
    wget curl ca-certificates libnss3 libx11-xcb1 libxcomposite1 libxdamage1 \
    libxrandr2 libgbm1 libgtk-3-0 libasound2 unzip xdg-utils git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Install Chromium browsers for Playwright
RUN playwright install chromium

# Copy app code
COPY . .

# Expose port
EXPOSE 8000

# Start Flask
CMD ["python", "app.py"]
