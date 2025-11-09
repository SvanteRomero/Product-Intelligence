FROM python:3.12-slim
WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY get_reddit_data.py .
COPY praw.ini .

# The -u flag ensures print statements appear in logs immediately
CMD ["python", "-u", "get_reddit_data.py"]