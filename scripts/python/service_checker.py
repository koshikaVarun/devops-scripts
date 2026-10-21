import argparse
import logging
import sys
import time
import requests

# Set up clean, timestamped logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def parse_cli_arguments():
    # argparse handles flags, defaults, and the built-in --help menu
    parser = argparse.ArgumentParser(
        description="Check website availability and response speed from the command line."
    )
    
    parser.add_argument(
        "--url",
        required=True,
        help="The target website or endpoint to test (e.g. https://httpbin.org/status/200)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=3.0,
        help="Maximum wait time in seconds before failing (default: 3.0)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed debug logs if enabled",
    )
    
    return parser.parse_args()

def run_service_check(url, timeout):
    logging.info(f"Target URL: {url}")
    logging.info(f"Configured timeout limit: {timeout}s")
    
    try:
        start_time = time.time()
        response = requests.get(url, timeout=timeout)
        elapsed = round(time.time() - start_time, 3)
        
        if response.status_code == 200:
            logging.info(f"Success! Status Code: {response.status_code} | Time: {elapsed}s")
            sys.exit(0)
        else:
            logging.warning(f"Unexpected status: {response.status_code} | Time: {elapsed}s")
            sys.exit(1)
            
    except requests.exceptions.Timeout:
        logging.error(f"Request timed out! Server took longer than {timeout}s to respond.")
        sys.exit(2)
    except requests.exceptions.RequestException as err:
        logging.error(f"Connection failed: {err}")
        sys.exit(3)

if __name__ == "__main__":
    args = parse_cli_arguments()
    
    # If the user passed --verbose, reveal detailed DEBUG messages
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Verbose debug logging enabled.")
        
    run_service_check(args.url, args.timeout)