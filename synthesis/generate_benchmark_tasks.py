#!/usr/bin/env python3
"""
Unified Benchmark Task Generation Script
Supports single-server, multi-server, or all modes
"""

import asyncio
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# Import the unified task generator
from synthesis.benchmark_generator import BenchmarkTaskGenerator


async def generate_single_server_tasks(
    generator: BenchmarkTaskGenerator, output_file: str
) -> Dict[str, Any]:
    """Generate single-server tasks with incremental saving"""
    print("Generating single-server tasks...")
    results = await generator.generate_single_server_tasks(output_file=output_file)
    print(f"Single-server tasks saved to: {output_file}")

    # Also save runner format
    runner_file = output_file.replace(".json", "_runner_format.json")
    generator.convert_single_to_runner_format(results, runner_file)
    print(f"Runner format saved to: {runner_file}")

    return results


async def generate_multi_server_tasks(
    generator: BenchmarkTaskGenerator, output_file: str, combinations_file: str = None
) -> Dict[str, Any]:
    """Generate multi-server tasks with incremental saving"""
    print("Generating multi-server tasks...")

    # If no combinations file specified, use default from split_combinations/
    if not combinations_file:
        # Default to 2-server combinations
        combinations_file = str(
            Path(__file__).parent
            / "split_combinations"
            / "mcp_2server_combinations.json"
        )
        print(f"Using default 2-server combinations file: {combinations_file}")
    else:
        print(f"Using combinations file: {combinations_file}")

    results = await generator.generate_multi_server_tasks(
        combinations_file=combinations_file, output_file=output_file
    )
    print(f"Multi-server tasks saved to: {output_file}")

    # Also save runner format
    runner_file = output_file.replace(".json", "_runner_format.json")
    generator.convert_multi_to_runner_format(results, runner_file)
    print(f"Runner format saved to: {runner_file}")

    return results


async def generate_specific_server_tasks(
    generator: BenchmarkTaskGenerator, server_name: str, output_file: str
) -> Dict[str, Any]:
    """Generate tasks for a specific server"""
    print(f"Generating tasks for server: {server_name}")
    print("-" * 50)

    # Check if server exists
    available_servers = [config.get("name") for config in generator.server_configs]
    if server_name not in available_servers:
        print(f"Error: Server '{server_name}' not found in configurations")
        print("Available servers:")
        for name in available_servers[:20]:  # Show first 20
            print(f"  - {name}")
        if len(available_servers) > 20:
            print(f"  ... and {len(available_servers) - 20} more")
        return None

    # Use the existing generate_single_server_tasks method with specific server
    results = await generator.generate_single_server_tasks(
        servers=[server_name],  # Pass as a list with single server
        output_file=output_file,
    )

    print(f"Tasks saved to: {output_file}")

    # Also save runner format
    runner_file = output_file.replace(".json", "_runner_format.json")
    generator.convert_single_to_runner_format(results, runner_file)
    print(f"Runner format saved to: {runner_file}")

    return results


async def generate_all_tasks(
    generator: BenchmarkTaskGenerator, output_dir: str, combinations_file: str = None
) -> Dict[str, Any]:
    """Generate all tasks (single, 2-server, and 3-server)"""
    date_str = datetime.now().strftime("%Y%m%d")
    output_dir = Path(output_dir)

    print("Generating all benchmark tasks...")
    print("-" * 50)

    # Generate single-server tasks
    print("\n[1/3] Single-server tasks:")
    single_file = output_dir / f"benchmark_tasks_{date_str}.json"
    single_results = await generate_single_server_tasks(generator, str(single_file))

    # Generate 2-server tasks
    print("\n[2/3] 2-server combination tasks:")
    if combinations_file:
        multi_2server_file = (
            output_dir / f"benchmark_multiserver_2server_tasks_{date_str}.json"
        )
        multi_2server_results = await generate_multi_server_tasks(
            generator, str(multi_2server_file), combinations_file
        )
    else:
        # Use default 2-server combinations
        combinations_2server = str(
            Path(__file__).parent
            / "split_combinations"
            / "mcp_2server_combinations.json"
        )
        multi_2server_file = (
            output_dir / f"benchmark_multiserver_2server_tasks_{date_str}.json"
        )
        multi_2server_results = await generate_multi_server_tasks(
            generator, str(multi_2server_file), combinations_2server
        )

    # Generate 3-server tasks
    print("\n[3/3] 3-server combination tasks:")
    combinations_3server = str(
        Path(__file__).parent / "split_combinations" / "mcp_3server_combinations.json"
    )
    multi_3server_file = (
        output_dir / f"benchmark_multiserver_3server_tasks_{date_str}.json"
    )
    multi_3server_results = await generate_multi_server_tasks(
        generator, str(multi_3server_file), combinations_3server
    )

    # Create combined summary
    combined_summary = {
        "generation_timestamp": datetime.now().isoformat(),
        "single_server": {
            "file": str(single_file),
            "total_servers": single_results.get("generation_info", {}).get(
                "total_servers", 0
            ),
            "successful_servers": single_results.get("generation_info", {}).get(
                "successful_servers", 0
            ),
            "failed_servers": single_results.get("generation_info", {}).get(
                "failed_servers", 0
            ),
            "total_tasks": sum(
                len(s.get("tasks", [])) for s in single_results.get("server_tasks", [])
            ),
        },
        "multi_server_2server": {
            "file": str(multi_2server_file),
            "total_combinations": multi_2server_results.get("generation_info", {}).get(
                "total_combinations", 0
            ),
            "successful_combinations": multi_2server_results.get(
                "generation_info", {}
            ).get("successful_combinations", 0),
            "failed_combinations": multi_2server_results.get("generation_info", {}).get(
                "failed_combinations", 0
            ),
            "total_tasks": multi_2server_results.get("generation_info", {}).get(
                "total_tasks", 0
            ),
        },
        "multi_server_3server": {
            "file": str(multi_3server_file),
            "total_combinations": multi_3server_results.get("generation_info", {}).get(
                "total_combinations", 0
            ),
            "successful_combinations": multi_3server_results.get(
                "generation_info", {}
            ).get("successful_combinations", 0),
            "failed_combinations": multi_3server_results.get("generation_info", {}).get(
                "failed_combinations", 0
            ),
            "total_tasks": multi_3server_results.get("generation_info", {}).get(
                "total_tasks", 0
            ),
        },
    }

    # Save summary
    summary_file = output_dir / f"benchmark_generation_summary_{date_str}.json"
    with open(summary_file, "w") as f:
        json.dump(combined_summary, f, indent=2)
    print(f"\nSummary saved to: {summary_file}")

    return combined_summary


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Unified Benchmark Task Generation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all tasks (default)
  python generate_benchmark_tasks.py

  # Generate only single-server tasks
  python generate_benchmark_tasks.py --mode single

  # Generate only multi-server tasks (defaults to 2-server combinations)
  python generate_benchmark_tasks.py --mode multi

  # Generate multi-server tasks with custom combinations file
  python generate_benchmark_tasks.py --mode multi --combinations-file synthesis/split_combinations/mcp_3server_combinations.json

  # Generate all tasks (single-server, 2-server, and 3-server combinations)
  python generate_benchmark_tasks.py --mode all

  # Generate without filtering problematic tools (filtering is enabled by default)
  python generate_benchmark_tasks.py --disable-filter-problematic

  # Generate multiple tasks per server/combination
  python generate_benchmark_tasks.py --tasks-per-combination 3

  # Process only first 5 servers (useful for testing)
  python generate_benchmark_tasks.py --total-servers 5

  # Skip first 10 servers and process next 5 (useful for resuming)
  python generate_benchmark_tasks.py --skip-servers 10 --total-servers 5

  # Specify custom output
  python generate_benchmark_tasks.py --output my_tasks.json
  python generate_benchmark_tasks.py --mode all --output ./results

  # Generate tasks for a specific server
  python generate_benchmark_tasks.py --server "OSINT Intelligence" --tasks-per-combination 2
  python generate_benchmark_tasks.py --server "Yahoo Finance" --disable-filter-problematic
        """,
    )

    parser.add_argument(
        "--mode",
        choices=["single", "multi", "all"],
        default="all",
        help="Generation mode: single-server, multi-server, or all (default: all)",
    )

    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (extension and mode suffix will be added automatically)",
    )

    parser.add_argument(
        "--disable-filter-problematic",
        action="store_true",
        help="Disable filtering of problematic tools during task synthesis (by default filters out problematic tools)",
    )

    parser.add_argument(
        "--tasks-per-combination",
        type=int,
        default=1,
        help="Number of tasks to generate per server/combination (default: 1)",
    )

    parser.add_argument(
        "--num-tasks",
        type=int,
        default=None,
        help="Total number of tasks to generate (overrides --tasks-per-combination if set)",
    )

    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum retry attempts for failed servers (default: 3)",
    )

    parser.add_argument(
        "--combinations-file",
        type=str,
        default=None,
        help="Path to the JSON file containing server combinations (default: auto-detect from split_combinations/)",
    )

    parser.add_argument(
        "--server",
        type=str,
        help='Generate tasks for a specific server only (e.g., "OSINT Intelligence")',
    )

    parser.add_argument(
        "--total-servers",
        type=int,
        default=None,
        help="Total number of servers to process (default: all servers, can also be set in config)",
    )

    parser.add_argument(
        "--skip-servers",
        type=int,
        default=None,
        help="Number of servers to skip at the beginning (default: 0, can also be set in config)",
    )

    args = parser.parse_args()

    # Determine tasks per server/combination
    if args.num_tasks is not None:
        tasks_per_server = args.num_tasks
    else:
        tasks_per_server = args.tasks_per_combination

    # Create unified generator
    generator = BenchmarkTaskGenerator(
        filter_problematic=not args.disable_filter_problematic,  # Default is True (enabled), flag disables it
        tasks_per_server=tasks_per_server,  # Works for both single server and combinations
        max_retries=args.max_retries,
        total_servers_limit=args.total_servers,  # None means use config or all servers
        skip_servers=args.skip_servers,  # None means use config or 0
    )

    try:
        date_str = datetime.now().strftime("%Y%m%d")

        # Handle specific server generation
        if args.server:
            if args.output:
                output_file = args.output
            else:
                # Clean server name for filename
                safe_server_name = (
                    args.server.replace(" ", "_").replace("/", "_").replace(":", "_")
                )
                output_file = f"benchmark_tasks_{safe_server_name}_{date_str}.json"

            results = await generate_specific_server_tasks(
                generator, args.server, output_file
            )

            if results:
                # Print summary
                server_tasks = results.get("server_tasks", [{}])[0]
                tasks = server_tasks.get("tasks", [])
                print("\n" + "=" * 50)
                print(f"Task generation completed for {args.server}!")
                print(f"Generated tasks: {len(tasks)}")
                print(f"Tools discovered: {server_tasks.get('tools_count', 0)}")
                print("=" * 50)
                return True
            else:
                print(f"\nFailed to generate tasks for {args.server}")
                return False

        elif args.mode == "single":
            # Generate single-server tasks only
            if args.output:
                output_file = args.output
            else:
                output_file = f"benchmark_tasks_{date_str}.json"
            results = await generate_single_server_tasks(generator, output_file)

            # Print summary
            info = results.get("generation_info", {})
            print("\n" + "=" * 50)
            print("Single-server task generation completed!")
            print(f"Total servers: {info.get('total_servers', 0)}")
            print(f"Successful: {info.get('successful_servers', 0)}")
            print(f"Failed: {info.get('failed_servers', 0)}")

        elif args.mode == "multi":
            # Generate multi-server tasks only
            if args.output:
                output_file = args.output
            else:
                output_file = f"benchmark_multiserver_tasks_{date_str}.json"
            results = await generate_multi_server_tasks(
                generator, output_file, args.combinations_file
            )

            # Print summary
            info = results.get("generation_info", {})
            print("\n" + "=" * 50)
            print("Multi-server task generation completed!")
            print(f"Total combinations: {info.get('total_combinations', 0)}")
            print(f"Successful: {info.get('successful_combinations', 0)}")
            print(f"Failed: {info.get('failed_combinations', 0)}")
            print(f"Total tasks: {info.get('total_tasks', 0)}")

        else:  # mode == 'all'
            # Generate all tasks
            if args.output:
                # Use output as base path/directory
                output_path = Path(args.output)
                if output_path.suffix:  # If it's a file, use its parent directory
                    output_dir = str(output_path.parent)
                else:  # If it's a directory path
                    output_dir = str(output_path)
            else:
                output_dir = "."
            summary = await generate_all_tasks(
                generator, output_dir, args.combinations_file
            )

            # Print final summary
            print("\n" + "=" * 50)
            print("All tasks generated successfully!")
            print("\nSingle-server summary:")
            print(f"  File: {summary['single_server']['file']}")
            print(
                f"  Servers: {summary['single_server']['successful_servers']}/{summary['single_server']['total_servers']}"
            )
            print(f"  Tasks: {summary['single_server']['total_tasks']}")
            print("\n2-Server combinations summary:")
            print(f"  File: {summary['multi_server_2server']['file']}")
            print(
                f"  Combinations: {summary['multi_server_2server']['successful_combinations']}/{summary['multi_server_2server']['total_combinations']}"
            )
            print(f"  Tasks: {summary['multi_server_2server']['total_tasks']}")
            print("\n3-Server combinations summary:")
            print(f"  File: {summary['multi_server_3server']['file']}")
            print(
                f"  Combinations: {summary['multi_server_3server']['successful_combinations']}/{summary['multi_server_3server']['total_combinations']}"
            )
            print(f"  Tasks: {summary['multi_server_3server']['total_tasks']}")

        return True

    except KeyboardInterrupt:
        print("\nGeneration interrupted by user")
        return False

    except Exception as e:
        print(f"\nError during generation: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv

    load_dotenv()

    # Run main program
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
