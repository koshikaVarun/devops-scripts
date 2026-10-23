FROM python:3.12-slim

WORKDIR /app

# Step 1: Copy dependencies and install them
COPY scripts/python/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Step 2: Copy the rest of the application files
COPY scripts/python/ /app/

# Step 3: Run the system audit script by default
CMD ["python3", "system_audit.py"]
