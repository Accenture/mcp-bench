from setuptools import setup, find_packages

setup(
    name="mcp_osint_server",
    version="0.1",
    packages=find_packages(),
    install_requires=["fastmcp"],
    entry_points={
        "console_scripts": [
            "mcp-osint=mcp_osint_server.main:main"
        ]
    },
    author="Himanshu sanecha",
    description="MCP OSINT Server with integrated tools like WHOIS, Nmap, Subfinder, etc.",
)
