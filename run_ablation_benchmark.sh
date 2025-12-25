#!/bin/bash
#
# Ablation Benchmark Runner for MCP-Bench
#
# This script runs benchmarks on ablation study tasks for:
#   - Single-server tasks
#   - 2-server combination tasks
#   - 3-server combination tasks
#
# It allows you to specify which models to test and which ablation study to use.
#
# Usage:
#   ./run_ablation_benchmark.sh --study <study_dir> --models <model1,model2,...>
#   ./run_ablation_benchmark.sh --study 20251207_155002 --models o4-mini
#   ./run_ablation_benchmark.sh --study 20251207_155002 --models o4-mini,gpt-4o --configs single,2server
#   ./run_ablation_benchmark.sh --list-studies
#   ./run_ablation_benchmark.sh --list-models
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ABLATION_DIR="${SCRIPT_DIR}/ablation_studies"

# Default values
STUDY=""
MODELS=""
CONFIGS="single,2server,3server"
LIST_STUDIES=false
LIST_MODELS=false
DISTRACTION_COUNT=""
VERBOSE=false
OUTPUT_DIR=""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print usage information
usage() {
    echo -e "${BLUE}Ablation Benchmark Runner for MCP-Bench${NC}"
    echo ""
    echo "Usage: $0 --study <study_dir> --models <model1,model2,...> [options]"
    echo ""
    echo "Required arguments (unless using --list-*):"
    echo "  --study <dir>              Ablation study directory name (e.g., 20251207_155002)"
    echo "                             Or 'latest' to use the most recent study"
    echo "  --models <models>          Comma-separated list of models to test"
    echo "                             Or 'all' to test all available models"
    echo ""
    echo "Optional arguments:"
    echo "  --configs <configs>        Server configurations to test (default: single,2server,3server)"
    echo "                             Options: single, 2server, 3server"
    echo "  --distraction-count <n>    Override distraction server count (default: use task's predefined)"
    echo "  --output-dir <dir>         Custom output directory for results"
    echo "  --verbose, -v              Enable verbose logging"
    echo "  --list-studies             List all available ablation studies"
    echo "  --list-models              List all available models"
    echo "  --help, -h                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  # Run all configurations with o4-mini on the latest study"
    echo "  $0 --study latest --models o4-mini"
    echo ""
    echo "  # Run only single-server tasks with multiple models"
    echo "  $0 --study 20251207_155002 --models o4-mini,gpt-4o --configs single"
    echo ""
    echo "  # Run 2-server and 3-server tasks with all available models"
    echo "  $0 --study latest --models all --configs 2server,3server"
    echo ""
    echo "  # List available studies and models"
    echo "  $0 --list-studies"
    echo "  $0 --list-models"
    echo ""
    echo "Available models (when API keys are configured):"
    echo "  OpenAI: o4-mini, gpt-4o, gpt-4o-mini, o3, gpt-5"
    echo "  Gemini: gemini-3-pro-preview, gemini-2.0-flash-exp, gemini-1.5-pro, gemini-1.5-flash"
    exit 1
}

# List available ablation studies
list_studies() {
    echo -e "${BLUE}Available Ablation Studies${NC}"
    echo ""

    if [[ ! -d "$ABLATION_DIR" ]]; then
        echo -e "${YELLOW}No ablation studies directory found.${NC}"
        echo "Run './run_ablation_study.sh' first to generate ablation study tasks."
        exit 0
    fi

    # Only list directories that match timestamp pattern (YYYYMMDD_HHMMSS)
    studies=$(ls -1d "$ABLATION_DIR"/*/ 2>/dev/null | xargs -n1 basename | grep -E '^[0-9]{8}_[0-9]{6}$' | sort -r)

    if [[ -z "$studies" ]]; then
        echo -e "${YELLOW}No ablation studies found.${NC}"
        echo "Run './run_ablation_study.sh' first to generate ablation study tasks."
        exit 0
    fi

    echo -e "${CYAN}Study Directory         Mode          Count    Tasks/Server${NC}"
    echo "--------------------------------------------------------------"

    for study in $studies; do
        metadata_file="$ABLATION_DIR/$study/ablation_metadata.json"
        if [[ -f "$metadata_file" ]]; then
            mode=$(python3 -c "import json; print(json.load(open('$metadata_file')).get('mode', 'N/A'))" 2>/dev/null || echo "N/A")
            count=$(python3 -c "import json; print(json.load(open('$metadata_file')).get('count', 'N/A'))" 2>/dev/null || echo "N/A")
            tasks_per=$(python3 -c "import json; print(json.load(open('$metadata_file')).get('tasks_per_server', 'N/A'))" 2>/dev/null || echo "N/A")
            printf "%-23s %-13s %-8s %s\n" "$study" "$mode" "$count" "$tasks_per"
        else
            printf "%-23s %-13s %-8s %s\n" "$study" "(no metadata)" "-" "-"
        fi
    done

    echo ""
    echo -e "${GREEN}Latest study:${NC} $(echo "$studies" | head -n1)"
}

# List available models
list_models() {
    echo -e "${BLUE}Available Models${NC}"
    echo ""

    cd "$SCRIPT_DIR"

    # Try to activate virtual environment if it exists
    if [[ -f "$SCRIPT_DIR/venv/bin/activate" ]]; then
        source "$SCRIPT_DIR/venv/bin/activate"
    elif [[ -f "$SCRIPT_DIR/.venv/bin/activate" ]]; then
        source "$SCRIPT_DIR/.venv/bin/activate"
    fi

    python3 -c "
import os
import sys
sys.path.insert(0, '.')
from llm.factory import LLMFactory

configs = LLMFactory.get_model_configs()
if not configs:
    print('No models available. Please set API keys:')
    print('  - OPENAI_API_KEY for OpenAI models')
    print('  - GEMINI_API_KEY for Gemini models')
else:
    print('Available models:')
    for i, (name, config) in enumerate(configs.items(), 1):
        print(f'  {i:2d}. {name} ({config.provider_type})')
    print(f'\nTotal: {len(configs)} models')
"
}

# Get latest study directory
get_latest_study() {
    if [[ ! -d "$ABLATION_DIR" ]]; then
        echo ""
        return
    fi

    # Only match directories with timestamp pattern (YYYYMMDD_HHMMSS)
    ls -1d "$ABLATION_DIR"/*/ 2>/dev/null | xargs -n1 basename | grep -E '^[0-9]{8}_[0-9]{6}$' | sort -r | head -n1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --study)
            STUDY="$2"
            shift 2
            ;;
        --models)
            MODELS="$2"
            shift 2
            ;;
        --configs)
            CONFIGS="$2"
            shift 2
            ;;
        --distraction-count)
            DISTRACTION_COUNT="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --list-studies)
            LIST_STUDIES=true
            shift
            ;;
        --list-models)
            LIST_MODELS=true
            shift
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

# Handle list options
if [[ "$LIST_STUDIES" == "true" ]]; then
    list_studies
    exit 0
fi

if [[ "$LIST_MODELS" == "true" ]]; then
    list_models
    exit 0
fi

# Validate required arguments
if [[ -z "$STUDY" ]]; then
    echo -e "${RED}Error: --study is required${NC}"
    usage
fi

if [[ -z "$MODELS" ]]; then
    echo -e "${RED}Error: --models is required${NC}"
    usage
fi

# Handle 'latest' study option
if [[ "$STUDY" == "latest" ]]; then
    STUDY=$(get_latest_study)
    if [[ -z "$STUDY" ]]; then
        echo -e "${RED}Error: No ablation studies found. Run './run_ablation_study.sh' first.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Using latest study: $STUDY${NC}"
fi

# Validate study directory exists
STUDY_DIR="$ABLATION_DIR/$STUDY"
if [[ ! -d "$STUDY_DIR" ]]; then
    echo -e "${RED}Error: Study directory not found: $STUDY_DIR${NC}"
    echo "Use --list-studies to see available studies."
    exit 1
fi

# Create output directory
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
if [[ -z "$OUTPUT_DIR" ]]; then
    OUTPUT_DIR="${STUDY_DIR}/benchmark_results_${TIMESTAMP}"
fi
mkdir -p "$OUTPUT_DIR"

# Print configuration
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}    MCP-Bench Ablation Benchmark Runner${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${BLUE}Configuration:${NC}"
echo "  Study: $STUDY"
echo "  Models: $MODELS"
echo "  Server configs: $CONFIGS"
echo "  Output directory: $OUTPUT_DIR"
if [[ -n "$DISTRACTION_COUNT" ]]; then
    echo "  Distraction count override: $DISTRACTION_COUNT"
fi
echo ""

# Read study metadata
METADATA_FILE="$STUDY_DIR/ablation_metadata.json"
if [[ -f "$METADATA_FILE" ]]; then
    echo -e "${BLUE}Study metadata:${NC}"
    python3 -c "
import json
with open('$METADATA_FILE') as f:
    meta = json.load(f)
    print(f\"  Mode: {meta.get('mode', 'N/A')}\")
    print(f\"  Count: {meta.get('count', 'N/A')}\")
    print(f\"  Tasks per server: {meta.get('tasks_per_server', 'N/A')}\")
"
    echo ""
fi

# Change to script directory
cd "$SCRIPT_DIR"

# Parse configs to run
IFS=',' read -ra CONFIG_ARRAY <<< "$CONFIGS"

# Track results
declare -A RUN_RESULTS

# Function to run benchmark for a specific configuration
run_benchmark() {
    local config_type="$1"
    local task_file=""
    local config_display=""

    case $config_type in
        single)
            task_file="$STUDY_DIR/ablation_single_server_tasks_runner_format.json"
            config_display="Single-server"
            ;;
        2server)
            task_file="$STUDY_DIR/ablation_2server_tasks_runner_format.json"
            config_display="2-server"
            ;;
        3server)
            task_file="$STUDY_DIR/ablation_3server_tasks_runner_format.json"
            config_display="3-server"
            ;;
        *)
            echo -e "${RED}Error: Unknown config type: $config_type${NC}"
            return 1
            ;;
    esac

    # Check if task file exists
    if [[ ! -f "$task_file" ]]; then
        echo -e "${YELLOW}Warning: Task file not found: $task_file${NC}"
        echo -e "${YELLOW}Skipping $config_display configuration.${NC}"
        RUN_RESULTS[$config_type]="skipped"
        return 0
    fi

    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}Running $config_display Benchmark${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo "  Task file: $task_file"
    echo ""

    # Build the command
    local cmd="python3 benchmark/runner.py"
    cmd+=" --tasks-file \"$task_file\""

    # Handle model selection
    if [[ "$MODELS" == "all" ]]; then
        cmd+=" --models all"
    else
        # Convert comma-separated to space-separated
        local models_spaced="${MODELS//,/ }"
        cmd+=" --models $models_spaced"
    fi

    # Add output file
    local output_file="$OUTPUT_DIR/${config_type}_results.json"
    cmd+=" --output \"$output_file\""

    # Add distraction count if specified
    if [[ -n "$DISTRACTION_COUNT" ]]; then
        cmd+=" --distraction-count $DISTRACTION_COUNT"
    fi

    # Add verbose flag if set
    if [[ "$VERBOSE" == "true" ]]; then
        cmd+=" --verbose"
    fi

    echo -e "${CYAN}Command: $cmd${NC}"
    echo ""

    # Run the benchmark
    if eval $cmd; then
        RUN_RESULTS[$config_type]="success"
        echo -e "${GREEN}$config_display benchmark completed successfully${NC}"
    else
        RUN_RESULTS[$config_type]="failed"
        echo -e "${RED}$config_display benchmark failed${NC}"
    fi

    echo ""
}

# Run benchmarks for each configuration
for config in "${CONFIG_ARRAY[@]}"; do
    config=$(echo "$config" | xargs)  # Trim whitespace
    run_benchmark "$config"
done

# Generate summary
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}           Benchmark Summary${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${BLUE}Study:${NC} $STUDY"
echo -e "${BLUE}Models:${NC} $MODELS"
echo -e "${BLUE}Output directory:${NC} $OUTPUT_DIR"
echo ""
echo -e "${BLUE}Results:${NC}"

for config in "${CONFIG_ARRAY[@]}"; do
    config=$(echo "$config" | xargs)
    result="${RUN_RESULTS[$config]:-not_run}"

    case $result in
        success)
            echo -e "  ${GREEN}[OK]${NC} $config"
            ;;
        failed)
            echo -e "  ${RED}[FAILED]${NC} $config"
            ;;
        skipped)
            echo -e "  ${YELLOW}[SKIPPED]${NC} $config"
            ;;
        *)
            echo -e "  ${YELLOW}[NOT RUN]${NC} $config"
            ;;
    esac
done

echo ""

# List generated result files
echo -e "${BLUE}Generated result files:${NC}"
ls -la "$OUTPUT_DIR"/*.json 2>/dev/null || echo "  (no result files generated)"

echo ""

# Create summary metadata
SUMMARY_FILE="$OUTPUT_DIR/benchmark_summary.json"
python3 << PYTHON_SCRIPT
import json
from datetime import datetime

summary = {
    "timestamp": "$TIMESTAMP",
    "study": "$STUDY",
    "models": "$MODELS".split(","),
    "configs_tested": "$CONFIGS".split(","),
    "output_directory": "$OUTPUT_DIR",
    "results": {
$(for config in "${CONFIG_ARRAY[@]}"; do
    config=$(echo "$config" | xargs)
    result="${RUN_RESULTS[$config]:-not_run}"
    echo "        \"$config\": \"$result\","
done)
    }
}

# Remove trailing comma from results dict
with open("$SUMMARY_FILE", "w") as f:
    json.dump(summary, f, indent=2)

print(f"Summary saved to: $SUMMARY_FILE")
PYTHON_SCRIPT

echo ""
echo -e "${GREEN}Ablation benchmark run complete!${NC}"
