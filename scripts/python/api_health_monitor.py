import sys
import time
import requests

# Endpoints configured for probing:
# 1. httpbin.org/status/200 -> Returns HTTP 200 (Healthy)
# 2. httpbin.org/delay/1    -> Responds with a 1-second latency (Latency Check)
# 3. httpbin.org/status/500 -> Simulates an internal server failure (Outage Alert)
# 4. httpbin.org/status/404 -> Simulates a missing resource
TARGET_SERVICES = [
    {"name": "Auth Gateway", "url": "https://httpbin.org/status/200", "expected_code": 200},
    {"name": "Billing Service", "url": "https://httpbin.org/delay/1", "expected_code": 200},
    {"name": "Inventory API", "url": "https://httpbin.org/status/500", "expected_code": 200},
    {"name": "Search Endpoint", "url": "https://httpbin.org/status/404", "expected_code": 200},
]

# SLA threshold in seconds (alert if latency exceeds this)
LATENCY_SLA_SECONDS = 1.5
REQUEST_TIMEOUT_SECONDS = 3.0

def probe_endpoints(endpoints):
    print("=" * 60)
    print(" SRE SYNTHETIC API HEALTH PROBE")
    print("=" * 60)

    unhealthy_services = []

    for svc in endpoints:
        name = svc["name"]
        url = svc["url"]
        expected = svc["expected_code"]

        try:
            start_time = time.time()
            response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
            latency = round(time.time() - start_time, 3)

            status_code = response.status_code

            # Check status code match and SLA latency
            if status_code == expected:
                if latency > LATENCY_SLA_SECONDS:
                    status_flag = "[WARN: HIGH LATENCY]"
                    unhealthy_services.append(f"{name} (Latency: {latency}s > SLA {LATENCY_SLA_SECONDS}s)")
                else:
                    status_flag = "[HEALTHY]"
            else:
                status_flag = f"[FAILED: Status {status_code}]"
                unhealthy_services.append(f"{name} (Expected {expected}, got {status_code})")

            print(f"{status_flag:<25} | {name:<18} | Code: {status_code:<3} | {latency}s")

        except requests.exceptions.Timeout:
            print(f"{'[CRITICAL: TIMEOUT]':<25} | {name:<18} | Timed out after {REQUEST_TIMEOUT_SECONDS}s")
            unhealthy_services.append(f"{name} (Request timed out)")
        except requests.exceptions.RequestException as e:
            print(f"{'[CRITICAL: CONN_ERR]':<25} | {name:<18} | Connection error: {e}")
            unhealthy_services.append(f"{name} (Connection failure)")

    print("=" * 60)

    if unhealthy_services:
        print(f"ALERT: {len(unhealthy_services)} service(s) breached SLA / health checks:")
        for issue in unhealthy_services:
            print(f"  -> {issue}")
        print("=" * 60)
        sys.exit(1)
    else:
        print("SUCCESS: All probed services are operational within SLA.")
        print("=" * 60)
        sys.exit(0)

if __name__ == "__main__":
    probe_endpoints(TARGET_SERVICES)