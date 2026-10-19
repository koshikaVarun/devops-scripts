import json
import yaml
import os
import sys

def process_infra_data(json_path, yaml_out_path):
    if not os.path.exists(json_path):
        print(f"ERROR: Cannot find config file '{json_path}'")
        sys.exit(1)

    # 1. Read & deserialize JSON
    with open(json_path, "r") as f:
        config = json.load(f)

    cluster = config.get("cluster_name", "unknown")
    env = config.get("environment", "unknown")
    nodes = config.get("nodes", [])

    total_cpu = 0
    total_mem = 0
    unhealthy_nodes = []

    # 2. Process node metrics
    for node in nodes:
        total_cpu += node["cpu_cores"]
        total_mem += node["memory_gb"]
        if node["status"] != "healthy":
            unhealthy_nodes.append(node["node_id"])

    print("=" * 50)
    print(f" CLUSTER AUDIT: {cluster.upper()} ({env})")
    print("=" * 50)
    print(f"Total Nodes Monitored : {len(nodes)}")
    print(f"Total CPU Capacity    : {total_cpu} vCPUs")
    print(f"Total Memory Capacity : {total_mem} GB RAM")
    print(f"Unhealthy Nodes       : {len(unhealthy_nodes)} -> {unhealthy_nodes}")

    # 3. Build a structured summary dictionary
    summary_report = {
        "metadata": {
            "cluster": cluster,
            "environment": env,
            "generated_by": "SRE Python Pipeline"
        },
        "capacity": {
            "total_nodes": len(nodes),
            "total_cpu_cores": total_cpu,
            "total_memory_gb": total_mem
        },
        "health_check": {
            "all_healthy": len(unhealthy_nodes) == 0,
            "flagged_nodes": unhealthy_nodes
        }
    }

    # 4. Serialize to YAML
    with open(yaml_out_path, "w") as out:
        yaml.dump(summary_report, out, default_flow_style=False, sort_keys=False)

    print(f"\n[+] Successfully generated YAML summary: {yaml_out_path}")
    print("=" * 50)

    # Return exit code 1 if degraded nodes exist
    if unhealthy_nodes:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    process_infra_data("infra_config.json", "cluster_summary.yaml")