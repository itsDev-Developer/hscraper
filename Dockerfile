FROM python:3.12-slim

# Install system dependencies for Chromium
RUN apt-get update && apt-get install -y \
    wget curl gnupg ca-certificates libnss3 libatk-bridge2.0-0 \
    libxkbcommon0 libx11-xcb1 libxcb1 libxcomposite1 libxdamage1 \
    libxrandr2 libgbm1 libgtk-3-0 libasound2 libpangocairo-1.0-0 \
    libatk1.0-0 libcups2 libdrm2 libxshmfence1 libpci3 libwoff1 \
    libopus0 libwebp6 libharfbuzz0b libvpx6 libwoff2-1 libjpeg-turbo8 \
    libpng16-16 libevent-2.1-7 unzip xdg-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Install playwright browsers
RUN playwright install chromium

COPY . .

EXPOSE 8000

CMD ["python", "app.py"]
