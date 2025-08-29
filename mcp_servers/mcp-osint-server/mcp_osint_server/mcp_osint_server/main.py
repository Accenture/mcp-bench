from fastmcp import FastMCP
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

# Create an MCP server instance named "OSINT Server"
mcp = FastMCP("OSINT Server")

# Define all the OSINT functions (WHOIS, Amass, Nmap, etc.)
@mcp.tool()
def whois_lookup(target: str) -> str:
    try:
        result = subprocess.run(["whois", target], capture_output=True, text=True, timeout=10000)
        return "WHOIS Lookup:\n" + (result.stdout if result.returncode == 0 else "Failed")
    except Exception as e:
        return f"Error during WHOIS lookup: {str(e)}"

@mcp.tool()
def nmap_scan(target: str) -> str:
    try:
        result = subprocess.run(["nmap", "-F", "-T4", target], capture_output=True, text=True, timeout=10000)
        return "Nmap Fast Scan:\n" + (result.stdout if result.returncode == 0 else "Failed")
    except Exception as e:
        return f"Error during Nmap scan: {str(e)}"

@mcp.tool()
def dnsrecon_lookup(target: str) -> str:
    try:
        result = subprocess.run(["dnsrecon", "-d", target], capture_output=True, text=True, timeout=10000)
        return "DNSRecon Results:\n" + (result.stdout if result.returncode == 0 else "Failed")
    except Exception as e:
        return f"Error during DNSRecon lookup: {str(e)}"

@mcp.tool()
def dnstwist_lookup(domain: str) -> str:
    try:
        result = subprocess.run(["dnstwist", domain], capture_output=True, text=True, timeout=10000)
        return result.stdout if result.returncode == 0 else "DNSTwist lookup failed."
    except Exception as e:
        return f"Error running DNSTwist: {str(e)}"

@mcp.tool()
def dig_lookup(target: str) -> str:
    try:
        result = subprocess.run(["dig", target], capture_output=True, text=True, timeout=10000)
        return "Dig Results:\n" + (result.stdout if result.returncode == 0 else "Failed")
    except Exception as e:
        return f"Error running Dig: {str(e)}"

@mcp.tool()
def host_lookup(target: str) -> str:
    try:
        result = subprocess.run(["host", target], capture_output=True, text=True, timeout=10000)
        return "Host Lookup Results:\n" + (result.stdout if result.returncode == 0 else "Failed")
    except Exception as e:
        return f"Error running Host lookup: {str(e)}"

# Parallel OSINT execution
@mcp.tool()
def osint_overview(target: str) -> str:
    tools = [
        whois_lookup,
        nmap_scan,
        dnsrecon_lookup,
        dnstwist_lookup,
        dig_lookup,
        host_lookup
    ]

    results = []
    with ThreadPoolExecutor() as executor:
        future_to_tool = {executor.submit(tool, target): tool.__name__ for tool in tools}
        for future in as_completed(future_to_tool):
            tool_name = future_to_tool[future]
            try:
                results.append(f"{tool_name}:{future.result()}")
            except Exception as e:
                results.append(f"{tool_name} failed with error: {str(e)}")

    return "\n\n".join(results)

# Main function to run the MCP server
def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()