import os
import sys
import logging
import requests
from dotenv import load_dotenv

# Set up standard logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Load variables from .env file into os.environ
load_dotenv()

def get_required_env(var_name):
    value = os.getenv(var_name)
    if not value:
        logging.error(f"Missing required environment variable: {var_name}")
        sys.exit(1)
    return value

def send_alert_notification(service_name, issue_detail):
    webhook_url = get_required_env("ALERT_WEBHOOK_URL")
    api_key = get_required_env("MONITOR_API_KEY")
    environment = os.getenv("ALERT_ENVIRONMENT", "development")

    logging.info(f"Target Environment: {environment}")
    logging.info(f"Preparing alert payload for {service_name}...")

    # Headers containing our authentication token
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "service": service_name,
        "environment": environment,
        "issue": issue_detail,
        "status": "CRITICAL",
    }

    try:
        logging.info("Sending alert to webhook endpoint...")
        response = requests.post(webhook_url, json=payload, headers=headers, timeout=5.0)

        if response.status_code == 200:
            logging.info("Alert successfully dispatched to notification channel! [Code 200]")
            sys.exit(0)
        else:
            logging.warning(f"Failed to post alert. Received status: {response.status_code}")
            sys.exit(1)

    except requests.exceptions.RequestException as err:
        logging.error(f"Network error during alert dispatch: {err}")
        sys.exit(2)

if __name__ == "__main__":
    send_alert_notification("Payment Gateway", "High latency: response time > 3.5s")