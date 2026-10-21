import argparse
import logging
import os
import platform
import re
import sys
import time
import json
import yaml
import requests
from dotenv import load_dotenv

# Set up clean, timestamped logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Load secrets from local .env
load_dotenv()

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="SRE Sentinel - Unified Host, Log, and Service Health Monitor"
    )
    parser.add_argument(
        "--log-file",
        default="access.log",
        help="Path to access log for regex error scanning (default: access.log)",
    )
    parser.add_argument(
        "--api-url",
        default="https://httpbin.org/status/200",
        help="External API endpoint to test (default: https://httpbin.org/status/200)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=3.0,
        help="HTTP probe timeout threshold in seconds (default: 3.0)",
    )
    parser.add_argument(
        "--output-yaml",
        default="sentinel_report.yaml",
        help="Path to save the generated health report (default: sentinel_report.yaml)",
    )
    return parser.parse_args()

def check_host_diagnostics():
    logging.info("Checking host system metrics...")
    return {
        "os_platform": platform.system(),
        "os_release": platform.release(),
        "cpu_logical_cores": os.cpu_count() or 1,
        "machine_architecture": platform.machine(),
    }

def scan_access_logs(log_path):
    logging.info(f"Scanning access log: {log_path}")
    if not os.path.exists(log_path):
        logging.warning(f"Log file '{log_path}' not found. Skipping log scan.")
        return {"status": "SKIPPED", "total_requests": 0, "server_5xx_errors": 0}

    log_pattern = re.compile(
        r'(?P<ip>\d+\.\d+\.\d+\.\d+).*?"(?P<method>[A-Z]+) (?P<url>[^\s]+).*?" (?P<status>\d{3})'
    )

    total_requests = 0
    errors_5xx = 0

    with open(log_path, "r") as f:
        for line in f:
            match = log_pattern.search(line.strip())
            if match:
                total_requests += 1
                status = int(match.group("status"))
                if 500 <= status < 600:
                    errors_5xx += 1

    logging.info(f"Log results: {total_requests} lines scanned, {errors_5xx} critical 5xx errors found.")
    return {
        "total_requests": total_requests,
        "server_5xx_errors": errors_5xx,
        "passed": errors_5xx == 0,
    }

def probe_target_api(url, timeout):
    logging.info(f"Probing target API endpoint: {url}")
    try:
        start = time.time()
        response = requests.get(url, timeout=timeout)
        duration = round(time.time() - start, 3)

        passed = response.status_code == 200
        logging.info(f"API probe finished in {duration}s with status {response.status_code}.")
        return {
            "target_url": url,
            "status_code": response.status_code,
            "latency_seconds": duration,
            "passed": passed,
        }
    except requests.exceptions.RequestException as err:
        logging.error(f"API probe failed: {err}")
        return {
            "target_url": url,
            "status_code": 0,
            "latency_seconds": 0.0,
            "passed": False,
            "error": str(err),
        }

def send_alert_notification(summary_issues):
    webhook_url = os.getenv("ALERT_WEBHOOK_URL")
    api_key = os.getenv("MONITOR_API_KEY", "default-key")
    env = os.getenv("ALERT_ENVIRONMENT", "production")

    if not webhook_url:
        logging.warning("ALERT_WEBHOOK_URL not configured in .env. Skipping alert dispatch.")
        return

    logging.info("Dispatched alert notification via webhook...")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "source": "SRE Sentinel",
        "environment": env,
        "issues": summary_issues,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    try:
        res = requests.post(webhook_url, json=payload, headers=headers, timeout=5.0)
        if res.status_code == 200:
            logging.info("Alert webhook acknowledged successfully [200 OK].")
        else:
            logging.warning(f"Alert webhook rejected with status: {res.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Could not reach alert webhook: {e}")

def run_sentinel():
    args = parse_arguments()

    print("=" * 60)
    print(" SRE SENTINEL: UNIFIED PRODUCTION HEALTH AUDIT")
    print("=" * 60)

    # 1. Run all checks
    host_data = check_host_diagnostics()
    log_data = scan_access_logs(args.log_file)
    api_data = probe_target_api(args.api_url, args.timeout)

    # 2. Identify failures
    issues_detected = []
    if not log_data.get("passed", True):
        issues_detected.append(f"Logs: {log_data['server_5xx_errors']} critical 5xx errors in {args.log_file}")
    if not api_data.get("passed", False):
        issues_detected.append(f"API: Endpoint {args.api_url} failed with status {api_data['status_code']}")

    overall_healthy = len(issues_detected) == 0

    # 3. Assemble structured report
    full_report = {
        "sentinel_meta": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "HEALTHY" if overall_healthy else "DEGRADED",
        },
        "host_system": host_data,
        "log_inspection": log_data,
        "service_probe": api_data,
        "issues": issues_detected,
    }

    # 4. Serialize report to YAML
    with open(args.output_yaml, "w") as out:
        yaml.dump(full_report, out, default_flow_style=False, sort_keys=False)

    logging.info(f"Structured health summary written to {args.output_yaml}")
    print("=" * 60)

    # 5. Handle alerting & exit codes
    if not overall_healthy:
        logging.warning("System health flagged DEGRADED. Initiating incident response...")
        for issue in issues_detected:
            print(f"  [!] {issue}")
        send_alert_notification(issues_detected)
        print("=" * 60)
        sys.exit(1)
    else:
        logging.info("All checks PASSED. Entire stack is healthy.")
        print("=" * 60)
        sys.exit(0)

if __name__ == "__main__":
    run_sentinel()