import re
import os
import sys

def parse_server_logs(file_path):
    if not os.path.exists(file_path):
        print(f"ERROR: Target log file '{file_path}' does not exist.")
        sys.exit(1)

    # Regex breakdown:
    # (?P<ip>\d+\.\d+\.\d+\.\d+)  -> Captures the client IP address
    # "(?P<method>[A-Z]+) (?P<url>[^\s]+) -> Captures HTTP method and endpoint
    # (?P<status>\d{3})           -> Captures the 3-digit HTTP status code
    log_pattern = re.compile(
        r'(?P<ip>\d+\.\d+\.\d+\.\d+).*?"(?P<method>[A-Z]+) (?P<url>[^\s]+).*?" (?P<status>\d{3})'
    )

    total_requests = 0
    errors_5xx = 0
    errors_4xx = 0
    incident_entries = []

    with open(file_path, "r") as log_file:
        for line in log_file:
            line = line.strip()
            if not line:
                continue
            
            match = log_pattern.search(line)
            if match:
                total_requests += 1
                data = match.groupdict()
                status_code = int(data["status"])

                if 500 <= status_code < 600:
                    errors_5xx += 1
                    incident_entries.append(data)
                elif 400 <= status_code < 500:
                    errors_4xx += 1

    print("=" * 50)
    print(" SRE INCIDENT LOG ANALYSIS REPORT")
    print("=" * 50)
    print(f"Total Requests Scanned : {total_requests}")
    print(f"Client Errors (4xx)    : {errors_4xx}")
    print(f"Server Failures (5xx)  : {errors_5xx}")

    if errors_5xx > 0:
        print("\n[!] CRITICAL: 5xx Server Outages Detected:")
        for incident in incident_entries:
            print(f"  -> IP: {incident['ip']} | Method: {incident['method']} | Endpoint: {incident['url']} | Status: {incident['status']}")
        print("=" * 50)
        print("STATUS: Log inspection flagged active 5xx anomalies.")
        # Non-zero exit code so alerting systems detect the breach
        sys.exit(2)
    else:
        print("\n[+] Health: No 5xx server failures detected.")
        print("=" * 50)
        sys.exit(0)

if __name__ == "__main__":
    parse_server_logs("access.log")