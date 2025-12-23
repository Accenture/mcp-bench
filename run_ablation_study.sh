#!/bin/bash
#
# Ablation Study Task Generator for MCP-Bench
#
# This script generates benchmark tasks for ablation studies with two modes:
#   1. Distraction mode: Specify the number of distraction servers
#   2. Total mode: Specify the total number of servers (required + distraction)
#
# Usage:
#   ./run_ablation_study.sh --mode distraction --count 5
#   ./run_ablation_study.sh --mode total --count 15
#   ./run_ablation_study.sh --mode distraction --count 5 --tasks-per-server 2
#

set -e

# Default values
MODE=""
COUNT=""
TASKS_PER_SERVER=1
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print usage information
usage() {
    echo -e "${BLUE}Ablation Study Task Generator for MCP-Bench${NC}"
    echo ""
    echo "Usage: $0 --mode <distraction|total> --count <number> [options]"
    echo ""
    echo "Required arguments:"
    echo "  --mode <distraction|total>  Generation mode:"
    echo "                              - distraction: Specify number of distraction servers"
    echo "                              - total: Specify total servers (required + distraction)"
    echo "  --count <number>            Number of servers based on mode"
    echo ""
    echo "Optional arguments:"
    echo "  --tasks-per-server <n>      Number of tasks per server/combination (default: 1)"
    echo "  --help                      Show this help message"
    echo ""
    echo "Examples:"
    echo "  # Generate tasks with 5 distraction servers"
    echo "  $0 --mode distraction --count 5"
    echo ""
    echo "  # Generate tasks with 15 total servers"
    echo "  $0 --mode total --count 15"
    echo ""
    echo "  # Generate 2 tasks per server with 10 distraction servers"
    echo "  $0 --mode distraction --count 10 --tasks-per-server 2"
    echo ""
    echo "Output:"
    echo "  Tasks are saved to: ablation_studies/YYYYMMDD_HHmmss/"
    echo "  Contains: single-server, 2-server, and 3-server task files"
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --count)
            COUNT="$2"
            shift 2
            ;;
        --tasks-per-server)
            TASKS_PER_SERVER="$2"
            shift 2
            ;;
        --help|-h)
            usage
            ;;
        *)
            echo -e "${RED}Error: Unknown argument: $1${NC}"
            usage
            ;;
    esac
done

# Validate required arguments
if [[ -z "$MODE" ]]; then
    echo -e "${RED}Error: --mode is required${NC}"
    usage
fi

if [[ -z "$COUNT" ]]; then
    echo -e "${RED}Error: --count is required${NC}"
    usage
fi

# Validate mode
if [[ "$MODE" != "distraction" && "$MODE" != "total" ]]; then
    echo -e "${RED}Error: Mode must be 'distraction' or 'total'${NC}"
    usage
fi

# Validate count is a positive integer
if ! [[ "$COUNT" =~ ^[0-9]+$ ]] || [[ "$COUNT" -lt 1 ]]; then
    echo -e "${RED}Error: Count must be a positive integer${NC}"
    usage
fi

# Validate tasks-per-server is a positive integer
if ! [[ "$TASKS_PER_SERVER" =~ ^[0-9]+$ ]] || [[ "$TASKS_PER_SERVER" -lt 1 ]]; then
    echo -e "${RED}Error: Tasks per server must be a positive integer${NC}"
    usage
fi

# Create timestamp for output directory (date,hours,minutes,seconds)
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_DIR="${SCRIPT_DIR}/ablation_studies/${TIMESTAMP}"

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}    MCP-Bench Ablation Study Generator${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${BLUE}Configuration:${NC}"
echo "  Mode: $MODE"
echo "  Count: $COUNT"
echo "  Tasks per server: $TASKS_PER_SERVER"
echo "  Output directory: $OUTPUT_DIR"
echo ""

# Create metadata file
METADATA_FILE="${OUTPUT_DIR}/ablation_metadata.json"
cat > "$METADATA_FILE" << EOF
{
    "timestamp": "$TIMESTAMP",
    "mode": "$MODE",
    "count": $COUNT,
    "tasks_per_server": $TASKS_PER_SERVER,
    "description": "Ablation study with $MODE mode, count=$COUNT"
}
EOF

echo -e "${BLUE}Metadata saved to: ${METADATA_FILE}${NC}"
echo ""

# Change to script directory
cd "$SCRIPT_DIR"

# Function to run Python task generator with custom distraction count
generate_tasks() {
    local task_type="$1"
    local output_file="$2"
    local distraction_count="$3"

    echo -e "${YELLOW}Generating ${task_type} tasks...${NC}"

    # Create a temporary Python script in the project root directory
    local temp_script="${SCRIPT_DIR}/_temp_ablation_generator.py"

    cat > "$temp_script" << 'PYTHON_SCRIPT'
#!/usr/bin/env python3
"""
Temporary script for ablation study task generation with custom distraction server count
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to path for imports (script is in project root)
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from synthesis.benchmark_generator import BenchmarkTaskGenerator

class AblationTaskGenerator(BenchmarkTaskGenerator):
    """Extended generator with configurable distraction server count"""

    def __init__(self, distraction_count=10, total_mode=False, **kwargs):
        super().__init__(**kwargs)
        self.distraction_count = distraction_count
        self.total_mode = total_mode

    def _select_distraction_servers(self, required_servers, count=None):
        """Override to use custom distraction count"""
        import random

        # Use the configured distraction count
        if self.total_mode:
            # In total mode, distraction = total - required
            actual_count = max(0, self.distraction_count - len(required_servers))
        else:
            # In distraction mode, use the count directly
            actual_count = self.distraction_count

        # Resident servers that are always available
        resident_servers = {"Time MCP"}

        # Create exclusion list
        exclude_list = set(required_servers) | resident_servers

        # Get available distraction candidates
        available_servers = [
            server for server in self.all_server_names if server not in exclude_list
        ]

        # Randomly select servers
        selected_count = min(actual_count, len(available_servers))
        selected_servers = random.sample(available_servers, selected_count) if selected_count > 0 else []

        # Sort for consistent output
        selected_servers.sort()

        return selected_servers


async def generate_single_tasks(generator, output_file):
    """Generate single-server tasks"""
    print(f"Generating single-server tasks to: {output_file}")
    results = await generator.generate_single_server_tasks(output_file=output_file)

    # Also save runner format
    runner_file = output_file.replace(".json", "_runner_format.json")
    generator.convert_single_to_runner_format(results, runner_file)
    print(f"Runner format saved to: {runner_file}")

    return results


async def generate_multi_tasks(generator, output_file, combinations_file):
    """Generate multi-server tasks"""
    print(f"Generating multi-server tasks to: {output_file}")
    results = await generator.generate_multi_server_tasks(
        combinations_file=combinations_file,
        output_file=output_file
    )

    # Also save runner format
    runner_file = output_file.replace(".json", "_runner_format.json")
    generator.convert_multi_to_runner_format(results, runner_file)
    print(f"Runner format saved to: {runner_file}")

    return results


async def main():
    if len(sys.argv) < 5:
        print("Usage: python _temp_generator.py <task_type> <output_file> <distraction_count> <total_mode> [tasks_per_server]")
        sys.exit(1)

    task_type = sys.argv[1]
    output_file = sys.argv[2]
    distraction_count = int(sys.argv[3])
    total_mode = sys.argv[4].lower() == "true"
    tasks_per_server = int(sys.argv[5]) if len(sys.argv) > 5 else 1

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Create generator with custom distraction count
    generator = AblationTaskGenerator(
        distraction_count=distraction_count,
        total_mode=total_mode,
        tasks_per_server=tasks_per_server,
        filter_problematic=True,
    )

    # Script is in project root
    script_dir = Path(__file__).parent

    if task_type == "single":
        await generate_single_tasks(generator, output_file)

    elif task_type == "2server":
        combinations_file = str(script_dir / "synthesis" / "split_combinations" / "mcp_2server_combinations.json")
        await generate_multi_tasks(generator, output_file, combinations_file)

    elif task_type == "3server":
        combinations_file = str(script_dir / "synthesis" / "split_combinations" / "mcp_3server_combinations.json")
        await generate_multi_tasks(generator, output_file, combinations_file)

    else:
        print(f"Unknown task type: {task_type}")
        sys.exit(1)

    print(f"Task generation completed for {task_type}")


if __name__ == "__main__":
    asyncio.run(main())
PYTHON_SCRIPT

    # Determine if total mode
    local total_mode="false"
    if [[ "$MODE" == "total" ]]; then
        total_mode="true"
    fi

    # Run the Python script
    python3 "$temp_script" "$task_type" "$output_file" "$distraction_count" "$total_mode" "$TASKS_PER_SERVER"

    local exit_code=$?

    # Clean up temp script
    rm -f "$temp_script"

    return $exit_code
}

# Generate all three task types
echo -e "${GREEN}Starting task generation...${NC}"
echo ""

# Track success/failure
SINGLE_SUCCESS=false
TWO_SERVER_SUCCESS=false
THREE_SERVER_SUCCESS=false

# 1. Generate single-server tasks
SINGLE_OUTPUT="${OUTPUT_DIR}/ablation_single_server_tasks.json"
if generate_tasks "single" "$SINGLE_OUTPUT" "$COUNT"; then
    SINGLE_SUCCESS=true
    echo -e "${GREEN}Single-server tasks generated successfully${NC}"
else
    echo -e "${RED}Failed to generate single-server tasks${NC}"
fi
echo ""

# 2. Generate 2-server tasks
TWO_SERVER_OUTPUT="${OUTPUT_DIR}/ablation_2server_tasks.json"
if generate_tasks "2server" "$TWO_SERVER_OUTPUT" "$COUNT"; then
    TWO_SERVER_SUCCESS=true
    echo -e "${GREEN}2-server tasks generated successfully${NC}"
else
    echo -e "${RED}Failed to generate 2-server tasks${NC}"
fi
echo ""

# 3. Generate 3-server tasks
THREE_SERVER_OUTPUT="${OUTPUT_DIR}/ablation_3server_tasks.json"
if generate_tasks "3server" "$THREE_SERVER_OUTPUT" "$COUNT"; then
    THREE_SERVER_SUCCESS=true
    echo -e "${GREEN}3-server tasks generated successfully${NC}"
else
    echo -e "${RED}Failed to generate 3-server tasks${NC}"
fi
echo ""

# Update metadata with results
cat > "$METADATA_FILE" << EOF
{
    "timestamp": "$TIMESTAMP",
    "mode": "$MODE",
    "count": $COUNT,
    "tasks_per_server": $TASKS_PER_SERVER,
    "description": "Ablation study with $MODE mode, count=$COUNT",
    "results": {
        "single_server": {
            "success": $SINGLE_SUCCESS,
            "file": "ablation_single_server_tasks.json",
            "runner_format": "ablation_single_server_tasks_runner_format.json"
        },
        "two_server": {
            "success": $TWO_SERVER_SUCCESS,
            "file": "ablation_2server_tasks.json",
            "runner_format": "ablation_2server_tasks_runner_format.json"
        },
        "three_server": {
            "success": $THREE_SERVER_SUCCESS,
            "file": "ablation_3server_tasks.json",
            "runner_format": "ablation_3server_tasks_runner_format.json"
        }
    }
}
EOF

# Print summary
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}           Generation Summary${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${BLUE}Output directory:${NC} $OUTPUT_DIR"
echo ""
echo -e "${BLUE}Generated files:${NC}"

if [[ "$SINGLE_SUCCESS" == "true" ]]; then
    echo -e "  ${GREEN}[OK]${NC} Single-server tasks"
else
    echo -e "  ${RED}[FAILED]${NC} Single-server tasks"
fi

if [[ "$TWO_SERVER_SUCCESS" == "true" ]]; then
    echo -e "  ${GREEN}[OK]${NC} 2-server tasks"
else
    echo -e "  ${RED}[FAILED]${NC} 2-server tasks"
fi

if [[ "$THREE_SERVER_SUCCESS" == "true" ]]; then
    echo -e "  ${GREEN}[OK]${NC} 3-server tasks"
else
    echo -e "  ${RED}[FAILED]${NC} 3-server tasks"
fi

echo ""
echo -e "${BLUE}Mode:${NC} $MODE"
if [[ "$MODE" == "distraction" ]]; then
    echo -e "${BLUE}Distraction servers:${NC} $COUNT per task"
else
    echo -e "${BLUE}Total servers:${NC} $COUNT (required + distraction)"
fi
echo ""

# List generated files
echo -e "${BLUE}Files in output directory:${NC}"
ls -la "$OUTPUT_DIR"

echo ""
echo -e "${GREEN}Ablation study generation complete!${NC}"
