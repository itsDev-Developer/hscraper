# Use Python 3.12 slim (compatible with greenlet)
FROM python:3.12-slim

# Install Chromium dependencies
RUN apt-get update && apt-get install -y \
    wget curl gnupg ca-certificates libnss3 libatk-bridge2.0-0 \
    libxkbcommon0 libx11-xcb1 libxcb1 libxcomposite1 libxdamage1 \
    libxrandr2 libgbm1 libgtk-3-0 libasound2 libpangocairo-1.0-0 \
    libatk1.0-0 libcups2 libdrm2 libxshmfence1 libpci3 libwoff1 \
    libopus0 libwebp6 libharfbuzz0b libvpx6 libwoff2-1 libjpeg-turbo8 \
    libpng16-16 libevent-2.1-7 unzip xdg-utils git && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Install Chromium browsers for Playwright
RUN playwright install chromium

# Copy app code
COPY . .

# Expose Flask port
EXPOSE 8000

# Start Flask
CMD ["python", "app.py"]
