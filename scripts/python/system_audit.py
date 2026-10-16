import os
import sys
import platform
import subprocess

def run_audit():
    print("=" * 45)
    print(" SRE SYSTEM HEALTH AUDIT (Python 3.12)")
    print("=" * 45)
    
    # 1. Platform & OS Metadata
    print(f"OS System     : {platform.system()} {platform.release()}")
    print(f"Architecture  : {platform.machine()}")
    print(f"Processor     : {platform.processor()}")
    print(f"Python Runtime: {sys.version.split()[0]}")
    print(f"Working Dir   : {os.getcwd()}")
    
    # 2. CPU Core Count
    cpu_cores = os.cpu_count()
    print(f"Logical CPUs  : {cpu_cores}")
    
    # 3. Subprocess Execution (Safe CLI command invocation)
    print("\n--- Network Hostname Verification ---")
    try:
        # Running 'hostname' via subprocess (standard across Windows/Linux)
        result = subprocess.run(["hostname"], capture_output=True, text=True, check=True)
        print(f"Host System Name: {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"Error checking hostname: {e}")
        sys.exit(1)

    print("=" * 45)
    print("STATUS: System audit completed successfully [Exit Code: 0]")
    print("=" * 45)

if __name__ == "__main__":
    run_audit()