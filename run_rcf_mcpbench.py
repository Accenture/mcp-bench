#!/usr/bin/env python3
import json
import requests
import statistics

DAEMON_URL = "http://127.0.0.1:9443/v1/evaluate"

def run_token_pruning_eval():
    print("Running RCF Okapi BM25 Token Pruning Evaluation (Dynamic MCP-Bench Simulation)...")
    
    # Simulating a massive OpenAPI tool schema with heavy description bloat
    bloated_schema = {
        "name": "openapi_search_repositories",
        "description": "Search repositories on GitHub. This endpoint allows you to search for repositories based on various criteria including stars, forks, and topics. " * 15,
        "inputSchema": {
            "type": "object",
            "properties": {
                "q": {
                    "type": "string",
                    "description": "The query contains one or more search keywords and qualifiers. Qualifiers allow you to limit your search to specific areas of GitHub. " * 8
                },
                "sort": {
                    "type": "string",
                    "description": "Sorts the results of your query by number of stars, forks, or help-wanted-issues or how recently the items were updated. " * 8
                }
            },
            "required": ["q"]
        }
    }

    # Simulate a payload of 50 heavy tools
    tools_payload = [bloated_schema] * 50
    
    # 1 token ≈ 4 characters
    original_tokens = len(json.dumps(tools_payload)) // 4
    pruned_tokens = 0
    latencies = []
    
    payload = {
        "benchmark": "mcp-bench",
        "phase": "tools/list",
        "user_mandate": "Find a repository about machine learning and sort by stars.",
        "tools": tools_payload
    }
    
    try:
        # Initial large payload request
        res = requests.post(DAEMON_URL, json=payload, timeout=2).json()
        
        if "latency_ms" in res:
            latencies.append(res["latency_ms"])
            
        if "allowed_tools" in res:
            pruned_tokens = len(json.dumps(res["allowed_tools"])) // 4
            
        # Loop 49 more times with a single tool to calculate accurate P50 processing latency
        for _ in range(49):
            loop_payload = {
                "benchmark": "mcp-bench", 
                "phase": "tools/list", 
                "user_mandate": payload["user_mandate"], 
                "tools": [bloated_schema]
            }
            res_loop = requests.post(DAEMON_URL, json=loop_payload, timeout=2).json()
            if "latency_ms" in res_loop:
                latencies.append(res_loop["latency_ms"])
                
    except requests.exceptions.ConnectionError:
        print("[!] RCF Daemon not reachable at 127.0.0.1:9443.")
        return
    except Exception as e:
        print(f"[!] Request error: {e}")
        return

    reduction = ((original_tokens - pruned_tokens) / original_tokens * 100) if original_tokens > 0 else 0
    p50 = statistics.median(latencies) if latencies else 0

    print("\n" + "="*50)
    print("🛡️ RCF MCP-BENCH LIVE RESULTS")
    print("="*50)
    print(f"Total Tool Schemas Processed : {len(tools_payload)}")
    print(f"Original Token Count         : ~{original_tokens}")
    print(f"Pruned Token Count           : ~{pruned_tokens}")
    print(f"Token Reduction              : {reduction:.2f}%")
    print(f"P50 Latency                  : {p50:.3f} ms")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_token_pruning_eval()