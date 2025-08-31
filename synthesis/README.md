# Task Synthesis

Generate benchmark tasks for MCP servers.

## Quick Start

### Generate Single-Server Tasks
```bash
nohup python synthesis/generate_benchmark_tasks.py \
  --mode single \
  --filter-problematic --tasks-per-combination 2 \
  --output benchmark_tasks_single_$(date +%Y%m%d)test.json \
  > task_generation_single_$(date +%Y%m%d)test.log 2>&1 &
```

### Generate Multi-Server Tasks (2 servers)
```bash
nohup python synthesis/generate_benchmark_tasks.py \
  --mode multi \
  --combinations-file synthesis/split_combinations/mcp_2server_combinations.json \
  --filter-problematic --tasks-per-combination 2 \
  --output benchmark_tasks_multi_2server_$(date +%Y%m%d)test.json \
  > task_generation_multi_2server_$(date +%Y%m%d)test.log 2>&1 &
```

### Generate Multi-Server Tasks (3 servers)
```bash
nohup python synthesis/generate_benchmark_tasks.py \
  --mode multi \
  --combinations-file synthesis/split_combinations/mcp_3server_combinations.json \
  --filter-problematic --tasks-per-combination 2 \
  --output benchmark_tasks_multi_3server_$(date +%Y%m%d)test.json \
  > task_generation_multi_3server_$(date +%Y%m%d)test.log 2>&1 &
```

## Files

- `task_synthesis.py` - Core task generation and fuzzy conversion
- `benchmark_generator.py` - Unified task generator for single/multi-server
- `generate_benchmark_tasks.py` - CLI script for batch generation
- `split_combinations/` - Pre-defined server combinations for multi-server tasks

## Output

Tasks are saved to `tasks/` directory in JSON format.