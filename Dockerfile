FROM python:3.12-slim

WORKDIR /app

# Dependencies layer (Cached)
COPY scripts/python/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Application source code layer
COPY scripts/python/ /app/

# ENTRYPOINT is the fixed executable that always runs
ENTRYPOINT ["python3", "sre_sentinel.py"]

# CMD provides the default arguments if none are passed
CMD ["--help"]
