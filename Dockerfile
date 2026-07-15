FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    libmupdf-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY day2/ ./day2/
COPY day3/ ./day3/
COPY day4/ ./day4/
COPY day5/ ./day5/
COPY day6/ ./day6/
COPY day7/ ./day7/
COPY day8/ ./day8/
COPY day9/ ./day9/
COPY day10/ ./day10/
COPY day11/ ./day11/

EXPOSE 8000

CMD ["python", "day10/persistent_api.py"]
