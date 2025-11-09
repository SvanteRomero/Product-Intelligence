# In crawler/Dockerfile

FROM python:3.12-slim
WORKDIR /usr/src/app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libnss3 libx11-xcb1 libdbus-1-3 libatk-bridge2.0-0 \
    libdrm2 libgbm1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install --with-deps

# This is the corrected line. It copies the *contents* of the
# product_intelligence folder into the current working directory.
COPY ./product_intelligence/ .

# Default command (can be overridden in docker-compose)
CMD ["scrapy", "crawl", "gsmarena"]