"""Task Executor Module.

This module orchestrates the multi-round execution of tasks using multiple MCP servers.
It handles planning, tool execution, state management, and result synthesis.

Classes:
    TaskExecutor: Main executor for multi-round task execution
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple

from llm.provider import LLMProvider
from mcp_modules.server_manager_persistent import PersistentMultiServerManager as MultiServerManager
from mcp_modules.connector import MCPConnector
from agent.execution_context import ExecutionContext
import config.config_loader as config_loader
from utils.error_handler import handle_errors

logger = logging.getLogger(__name__)

class TaskExecutor:
    """Orchestrates multi-round execution of tasks using multiple MCP servers.
    
    This class manages the execution lifecycle of complex tasks that may require
    multiple rounds of tool calls across different servers. It handles planning,
    execution, state management, and result synthesis.
    
    Attributes:
        llm: LLM provider for task planning and synthesis
        server_manager: Manager for MCP server connections
        all_tools: Dictionary of all available tools from servers
        concurrent_summarization: Whether to summarize results concurrently
        execution_results: List of all execution results
        accumulated_information: Accumulated information from all rounds
        _last_planning_info: Information about the last planning round
        
    Example:
        >>> executor = TaskExecutor(llm_provider, server_manager)
        >>> result = await executor.execute("Find weather in Tokyo")
    """

    def __init__(
        self, 
        llm_provider: LLMProvider, 
        server_manager: MultiServerManager, 
        concurrent_summarization: bool = False
    ) -> None:
        self.llm = llm_provider
        self.server_manager = server_manager
        self.all_tools = server_manager.all_tools
        self.concurrent_summarization = concurrent_summarization
        self.execution_results: List[Dict[str, Any]] = []
        self.accumulated_information = ""
        # Keep uncompressed version for judge evaluation
        self.accumulated_information_uncompressed = ""
        self._last_planning_info: Optional[Dict[str, Any]] = None
        
        # Planning JSON compliance tracking
        self._total_planned_tools = 0
        self._valid_planned_tools = 0
        
        # Token usage tracking
        self.total_output_tokens = 0
        self.total_prompt_tokens = 0
        self.total_tokens = 0

    async def execute(self, task: str) -> Dict[str, Any]:
        """Execute a task through multiple rounds of planning and tool calls.
        
        This is the main entry point for task execution. It manages the multi-round
        execution loop, calling tools as needed and accumulating information until
        the task is complete.
        
        Args:
            task: Natural language description of the task to execute
            
        Returns:
            Dictionary containing:
                - solution: Final synthesized solution
                - total_rounds: Number of execution rounds
                - execution_results: List of all tool execution results
                - planning_json_compliance: Ratio of valid to total planned tools
                - accumulated_information: All gathered information
                
        Raises:
            RuntimeError: If execution fails after maximum rounds
        """
        logger.info(f"Starting multi-server execution for task: \"{task}\"")
        
        # Log token consumption statistics for tool descriptions and input schemas
        self._log_tools_token_stats()
        
        
        self._last_planning_info = {
            'mode': 'multi-round',
            'rounds': []
        }
        
        max_rounds = config_loader.get_max_execution_rounds()
        for round_num in range(1, max_rounds + 1):
            logger.info(f"--- Starting Round {round_num}/{max_rounds} ---")

            should_continue, reasoning, round_executions = await self._plan_next_actions(task, round_num)
            
            round_planning_info = {
                'round_number': round_num,
                'should_continue': should_continue,
                'reasoning': reasoning
            }
            self._last_planning_info['rounds'].append(round_planning_info)
            
            logger.info(f"Decision: {'CONTINUE' if should_continue else 'STOP'}. Reasoning: {reasoning}")

            if not should_continue:
                logger.info(f"Stopping execution after {round_num-1} rounds.")
                break

            if not round_executions:
                logger.info(f"No tool executions planned for round {round_num}. Stopping.")
                break

            round_results = await self._execute_planned_tools(round_executions, round_num)
            await self._update_state(round_results, round_num)

        final_solution = await self._synthesize_final_solution(task, len(self.execution_results))
        logger.info("Multi-server execution finished.")
        
        # Calculate planning JSON compliance
        planning_json_compliance = (self._valid_planned_tools / self._total_planned_tools) if self._total_planned_tools > 0 else 1.0
        
        logger.info(f"Planning JSON Compliance: {self._valid_planned_tools}/{self._total_planned_tools} = {planning_json_compliance:.2%}")
        
        return {
            "solution": final_solution,
            "total_rounds": round_num - 1,
            "execution_results": self.execution_results,
            "planning_json_compliance": planning_json_compliance,
            "accumulated_information": self.accumulated_information,
            # Include uncompressed version for judge evaluation
            "accumulated_information_uncompressed": self.accumulated_information_uncompressed,
            # Token usage statistics
            "total_output_tokens": self.total_output_tokens,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_tokens": self.total_tokens
        }

    def _build_execution_summary(self) -> str:
        """Build execution summary for prompt."""
        if self.execution_results:
            return f"\nACCUMULATED INFORMATION:\n{self.accumulated_information if self.accumulated_information else 'No information gathered yet.'}\n"
        else:
            return "\nThis is the first round - no previous execution results."

    def _build_planning_prompt(self, task: str, round_num: int, execution_summary: str) -> str:
        """Build planning prompt."""
        return f"""You are a strategic decision-making expert for a multi-tool AI agent using the provided tools to perform the task.
        
        TASK: "{task}"
        CURRENT ROUND: {round_num}
        AVAILABLE TOOLS ACROSS SERVERS:
        {MCPConnector.format_tools_for_prompt(self.all_tools)}
        {execution_summary}
        
        DECISION AND PLANNING:
        1. Assess if the original task is fully completed
        2. If not complete, decide if another round would provide significant value
        3. If continuing, plan PARALLEL tool executions for this round
        
        PARALLEL EXECUTION PLANNING (if continuing):
        - Plan ALL tool calls for this round to execute in PARALLEL
        - ALL tools in this round will run simultaneously without dependencies
        - EARLY EXECUTION PRINCIPLE: Plan all necessary tool calls that don't require dependencies from other tools in this round
        - AVOID REDUNDANT CALLS: Don't repeat successful tools unless specifically needed
        - BUILD ON PREVIOUS RESULTS: Use information from previous rounds
        - FOCUS ON INDEPENDENT TASKS: Plan tools that can work with currently available information
        - You only have {config_loader.get_max_execution_rounds()} rounds in total for solving the task.

        Return your response in this exact JSON format:
        {{
            "reasoning": "<Detailed explanation for your decision and parallel execution plan>",
            "should_continue": <true/false>,
            "planned_tools": [
                {{
                    "tool": "server:tool_name",
                    "parameters": {{ "param": "value" }}
                }}
            ]
        }}
        
        PARALLEL EXECUTION RULES:
        - ALL tools in this round will run simultaneously
        - NO dependencies between tools within the same round
        - Each tool should work independently with available information
        
        If not continuing, set "planned_tools" to an empty array [].
        If continuing but no executions needed, also set "planned_tools" to an empty array [].
        Return ONLY the JSON object.
        """

    async def _fix_invalid_json_format(self, response_str: str, result: Any, round_num: int) -> dict:
        """Fix invalid JSON format from LLM response."""
        logger.warning(f"Attempting to fix invalid format for round {round_num}: {type(result)}")
        
        # Build correction prompt
        fix_prompt = f"""
        The previous response was not in the correct JSON format.
        Original response: {response_str}
        
        Please convert it to this exact format:
        {{
            "reasoning": "<explanation of decision and plan>",
            "should_continue": <true/false>,
            "planned_tools": [
                {{
                    "tool": "server:tool_name",
                    "parameters": {{}}
                }}
            ]
        }}
        
        If the original response was a list of tools, put them in "planned_tools".
        Return ONLY the corrected JSON object.
        """
        
        try:
            # Use LLM to fix the format
            fixed_response = await self.llm.get_completion(
                "You are a JSON format corrector. Convert the input to the specified JSON structure.",
                fix_prompt,
                config_loader.get_format_conversion_tokens()  # Small token limit for format conversion
            )
            fixed_result = self.llm.clean_and_parse_json(fixed_response)
            
            # Validate the fixed result
            if isinstance(fixed_result, dict) and "should_continue" in fixed_result:
                logger.info(f"Successfully fixed JSON format for round {round_num}")
                return fixed_result
        except Exception as fix_error:
            logger.error(f"Failed to fix JSON format via LLM: {fix_error}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Fallback: provide default structure based on the invalid result
        if isinstance(result, list):
            return {
                "reasoning": "LLM returned list format, assumed as planned_tools",
                "should_continue": len(result) > 0 and round_num < config_loader.get_max_execution_rounds(),
                "planned_tools": result
            }
        else:
            return {
                "reasoning": "Failed to parse LLM response",
                "should_continue": False,
                "planned_tools": []
            }

    async def _plan_next_actions(self, task: str, round_num: int) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """Multi-layered retry strategy for planning with ExecutionContext management."""
        logger.info(f"Planning next actions for round {round_num}")
        
        # Create new execution context for each planning call
        ctx = ExecutionContext()
        original_max_tokens = config_loader.get_planning_tokens()
        
        # Multi-layered retry strategy
        while ctx.can_retry_task():
            # Only show retry message if this is actually a retry (not the first attempt)
            if ctx.current_task_retry > 1:
                logger.info(f"Task retry {ctx.current_task_retry}/{ctx.max_task_retries} - {ctx.get_status_summary()}")
            
            while ctx.can_retry_round():
                # Only show round message if this is actually a retry (not the first round)
                if ctx.current_round > 1:
                    logger.info(f"Round retry {ctx.current_round}/{ctx.max_rounds} - {ctx.get_status_summary()}")
                
                # Build initial prompt
                execution_summary = self._build_execution_summary()
                prompt = self._build_planning_prompt(task, round_num, execution_summary)
                system_prompt = f"You are a strategic multi-tool AI agent planner for Round {round_num}. Plan parallel execution of independent tools for this round."
                
                # Retry with token reduction and format fixes
                result = None  # Initialize result
                while True:
                    try:
                        # Apply token reduction if needed
                        current_max_tokens = original_max_tokens
                        if ctx.current_token_reduction > 0:
                            current_max_tokens = ctx.apply_token_reduction(original_max_tokens)
                        
                        # Make LLM call with token tracking
                        response_data = await self.llm.get_completion(
                            system_prompt, 
                            prompt, 
                            current_max_tokens,
                            return_usage=True
                        )
                        
                        # Handle both tuple and string returns
                        if isinstance(response_data, tuple):
                            response_str, usage = response_data
                            if usage:
                                self.total_output_tokens += usage.get('completion_tokens', 0)
                                self.total_prompt_tokens += usage.get('prompt_tokens', 0)
                                self.total_tokens += usage.get('total_tokens', 0)
                        else:
                            response_str = response_data
                        
                        # Check for empty response
                        if not response_str or response_str.strip() == "":
                            if ctx.can_compress():
                                logger.info("Empty response detected, triggering compression...")
                                if await self.compress_accumulated_information():
                                    ctx.mark_compressed()
                                    ctx.current_token_reduction = 0  # Reset token reduction
                                    execution_summary = self._build_execution_summary()
                                    prompt = self._build_planning_prompt(task, round_num, execution_summary)
                                    continue
                            raise ValueError("Empty response received from LLM")
                        
                        # Parse JSON
                        try:
                            result = self.llm.clean_and_parse_json(response_str)
                        except Exception as parse_error:
                            logger.warning(f"JSON parse error: {parse_error}")
                            result = None
                        
                        # Check format and fix if needed
                        if not isinstance(result, dict) or "should_continue" not in result:
                            if ctx.can_fix_format():
                                ctx.increment_format_fixes()
                                logger.info(f"Invalid format detected, attempting fix {ctx.current_format_fixes}/{ctx.max_format_fixes}")
                                result = await self._fix_invalid_json_format(response_str, result, round_num)
                                
                                if isinstance(result, dict) and "should_continue" in result:
                                    logger.info("Format fix successful")
                                    break  # Success
                                else:
                                    continue  # Try format fix again
                            else:
                                logger.warning("Format fix attempts exhausted")
                                result = None
                                break  # Exit inner loop
                        else:
                            logger.info("Planning successful")
                            break  # Success
                    
                    except Exception as e:
                        error_msg = str(e)
                        logger.error(f"ERROR in planning attempt: {e}")
                        import traceback
                        logger.error(f"Full traceback: {traceback.format_exc()}")
                        
                        # Check for token limit errors
                        if self._is_token_limit_error(error_msg):
                            if ctx.can_reduce_tokens():
                                ctx.current_token_reduction += 1
                                logger.info(f"Token limit error, applying reduction {ctx.current_token_reduction}/{ctx.max_token_reductions}")
                                continue  # Retry with reduced tokens
                            elif ctx.can_compress():
                                logger.info("Token reduction exhausted, triggering compression...")
                                if await self.compress_accumulated_information():
                                    ctx.mark_compressed()
                                    ctx.current_token_reduction = 0
                                    execution_summary = self._build_execution_summary()
                                    prompt = self._build_planning_prompt(task, round_num, execution_summary)
                                    continue
                        
                        # For other errors, check if compression is available
                        elif ctx.can_compress():
                            logger.info(f"Planning error, triggering compression: {e}")
                            if await self.compress_accumulated_information():
                                ctx.mark_compressed()
                                ctx.current_token_reduction = 0
                                execution_summary = self._build_execution_summary()
                                prompt = self._build_planning_prompt(task, round_num, execution_summary)
                                continue
                        
                        # No more retries possible
                        result = None
                        break
                
                # Check if we got a valid result
                if isinstance(result, dict) and "should_continue" in result:
                    # Success! Return the result
                    should_continue = result.get("should_continue", round_num <= 1)
                    reasoning = result.get("reasoning", "No reasoning provided.")
                    planned_tools = result.get("planned_tools", [])
                    
                    executions = []
                    if isinstance(planned_tools, list):
                        for tool_plan in planned_tools:
                            if isinstance(tool_plan, dict):
                                self._total_planned_tools += 1
                                if tool_plan.get('tool'):
                                    self._valid_planned_tools += 1
                                    executions.append(tool_plan)
                    
                    logger.info(f"Planning successful - Continue={should_continue}, Planned {len(executions)} executions")
                    return should_continue, reasoning, executions
                
                # Round failed, try next round
                if ctx.can_retry_round():
                    logger.info("Round failed, waiting 60 seconds before next round...")
                    await asyncio.sleep(60)
                    ctx.start_new_round()
                else:
                    break  # No more rounds
            
            # All rounds failed, try new task retry
            if ctx.can_retry_task():
                logger.info("All rounds failed, starting new task retry...")
                ctx.start_new_task_retry()
            else:
                break  # No more task retries
        
        # All retries exhausted
        logger.error(f"All retry attempts exhausted for round {round_num}")
        return False, "All planning attempts failed", []


    async def _execute_planned_tools(self, executions: List[Dict[str, Any]], round_num: int) -> List[Dict[str, Any]]:
        """Executes a list of planned tool calls, handling sequential-only tools separately."""
        logger.info(f"Executing {len(executions)} planned tools for round {round_num}.")
        
        # Get sequential-only tools from config
        sequential_only_tools = config_loader.get_sequential_only_tools()
        
        # Separate sequential and concurrent executions
        sequential_executions = []
        concurrent_executions = []
        
        for exec in executions:
            tool_name = exec.get("tool")
            if tool_name in sequential_only_tools:
                sequential_executions.append(exec)
            else:
                concurrent_executions.append(exec)
        
        logger.info(f"Sequential tools: {len(sequential_executions)}, Concurrent tools: {len(concurrent_executions)}")
        
        # Group concurrent executions by server
        server_executions = {}
        for exec in concurrent_executions:
            tool_name = exec.get("tool")
            if tool_name and tool_name in self.all_tools:
                server_name = self.all_tools[tool_name]["server"]
            else:
                server_name = "unknown"
            
            if server_name not in server_executions:
                server_executions[server_name] = []
            server_executions[server_name].append(exec)
        
        server_semaphores = {server: asyncio.Semaphore(config_loader.get_server_semaphore_limit()) for server in server_executions}
        
        async def execute_one(execution: Dict[str, Any], semaphore: asyncio.Semaphore) -> Dict[str, Any]:
            async with semaphore:
                tool_name = execution.get("tool")
                params = execution.get("parameters", {})
                
                if not tool_name or tool_name not in self.all_tools:
                    error_msg = f"Tool '{tool_name}' not found or not specified."
                    logger.error(f"  - {error_msg}")
                    return {"tool": tool_name, "parameters": params, "round_num": round_num, "error": error_msg, "success": False}

                try:
                    result_obj = await self.server_manager.call_tool(tool_name, params)
                    
                    is_error = hasattr(result_obj, 'isError') and result_obj.isError
                    result_text = self._extract_text_from_result(result_obj)

                    server_name = self.all_tools[tool_name]["server"]

                    if is_error:
                        logger.warning(f"  - Tool `{tool_name}` on {server_name} failed with error: {result_text[:config_loader.get_error_display_prefix()]}...")
                        return {"tool": tool_name, "server": server_name, "parameters": params, "round_num": round_num, "error": result_text, "success": False}
                    else:
                        logger.info(f"  - Tool `{tool_name}` on {server_name} call successful.")
                        # Print tool return value (max 1000 chars)
                        result_preview = result_text[:1000] + "..." if len(result_text) > 1000 else result_text
                        logger.info(f"    Tool result: {result_preview}")
                        return {"tool": tool_name, "server": server_name, "parameters": params, "round_num": round_num, "result": result_text, "success": True}

                except Exception as e:
                    logger.error(f"ERROR in tool call '{tool_name}': {e}")
                    import traceback
                    logger.error(f"Full traceback: {traceback.format_exc()}")
                    server_name = self.all_tools.get(tool_name, {}).get("server", "unknown")
                    return {"tool": tool_name, "server": server_name, "parameters": params, "round_num": round_num, "error": str(e), "success": False}
        
        # Execute sequential tools first (one by one)
        sequential_results = []
        if sequential_executions:
            logger.info(f"Executing {len(sequential_executions)} sequential tools...")
            dummy_semaphore = asyncio.Semaphore(1)  # Limit to 1 to ensure sequential execution
            for exec in sequential_executions:
                logger.info(f"  Executing sequential tool: {exec.get('tool')}")
                result = await execute_one(exec, dummy_semaphore)
                sequential_results.append(result)
                logger.info(f"  Sequential tool {exec.get('tool')} completed: {'SUCCESS' if result.get('success') else 'FAILED'}")
        
        # Execute concurrent tools (existing logic)
        concurrent_results = []
        if concurrent_executions:
            logger.info(f"Executing {len(concurrent_executions)} concurrent tools...")
            execution_requests = []
            for server, server_execs in server_executions.items():
                semaphore = server_semaphores.get(server, asyncio.Semaphore(config_loader.get_server_semaphore_limit()))
                for exec in server_execs:
                    execution_requests.append(execute_one(exec, semaphore))
            
            concurrent_results = await asyncio.gather(*execution_requests)
        
        # Combine results maintaining execution order
        results = sequential_results + concurrent_results
        
        # Validate that all results are dictionaries with required fields
        for i, result in enumerate(results):
            if not isinstance(result, dict):
                raise RuntimeError(f"Tool execution {i} returned {type(result)} instead of dict - this is a bug")
            if 'success' not in result:
                raise RuntimeError(f"Tool execution {i} missing 'success' field - this is a bug")
            if 'tool' not in result:
                raise RuntimeError(f"Tool execution {i} missing 'tool' field - this is a bug")
        
        return results

    async def _update_state(self, round_results: List[Dict[str, Any]], round_num: int) -> None:
        """Update the accumulated information and execution results after a round.
        
        Args:
            round_results: List of execution results from the current round
            round_num: Current round number
            
        Raises:
            RuntimeError: If round results have invalid format
        """
        # Validate round_results before adding to execution_results
        for i, result in enumerate(round_results):
            if not isinstance(result, dict):
                raise RuntimeError(f"Round {round_num} result {i} is {type(result)} instead of dict - this is a bug")
            if 'success' not in result or 'tool' not in result:
                raise RuntimeError(f"Round {round_num} result {i} missing required fields - this is a bug")
        
        self.execution_results.extend(round_results)
        
        round_summary = f"\n\n--- Summary of Round {round_num} ---\n"
        
        if self.concurrent_summarization:
            # Concurrent summarization mode
            logger.info(f"Using concurrent summarization for {len(round_results)} results")
            
            async def process_result_concurrent(result):
                server = result.get('server', 'unknown')
                tool_name = result['tool']
                parameters = result.get('parameters', {})
                
                # Format parameters for display
                params_str = f"{parameters}" if parameters else "{}"
                
                if result['success']:
                    content = result['result']
                    token_count = self._estimate_token_count(content)
                    
                    if token_count <= config_loader.get_content_summary_threshold():
                        return f"Tool `{tool_name}` with Parameter {params_str} on {server} succeeded. Result: {content}\n"
                    else:
                        logger.info(f"Summarizing large result from {tool_name} ({token_count} tokens)")
                        try:
                            summarized_content = await self._summarize_content(content, "result")
                            return f"Tool `{tool_name}` with Parameter {params_str} on {server} succeeded. Result (summarized from {token_count} tokens): {summarized_content[:config_loader.get_content_truncate_length()]}\n"
                        except Exception as e:
                            logger.error(f"ERROR in summarizing result from {tool_name}: {e}")
                            import traceback
                            logger.error(f"Full traceback: {traceback.format_exc()}")
                            return f"Tool `{tool_name}` with Parameter {params_str} on {server} succeeded. Result (truncated): {content[:config_loader.get_content_truncate_length()]}...\n"
                else:
                    error_content = result['error']
                    token_count = self._estimate_token_count(error_content)
                    
                    if token_count <= config_loader.get_content_summary_threshold():
                        return f"Tool `{tool_name}` with Parameter {params_str} on {server} failed. Error: {error_content}\n"
                    else:
                        logger.info(f"Summarizing large error from {tool_name} ({token_count} tokens)")
                        try:
                            summarized_error = await self._summarize_content(error_content, "error")
                            return f"Tool `{tool_name}` with Parameter {params_str} on {server} failed. Error (summarized from {token_count} tokens): {summarized_error[:config_loader.get_error_truncate_length()]}\n"
                        except Exception as e:
                            logger.error(f"ERROR in summarizing error from {tool_name}: {e}")
                            import traceback
                            logger.error(f"Full traceback: {traceback.format_exc()}")
                            return f"Tool `{tool_name}` with Parameter {params_str} on {server} failed. Error (truncated): {error_content[:config_loader.get_error_truncate_length()]}...\n"
            
            # Process all results concurrently
            result_summaries = await asyncio.gather(
                *[process_result_concurrent(result) for result in round_results],
                return_exceptions=True
            )
            
            # Add all summaries to round_summary
            for summary in result_summaries:
                if isinstance(summary, str):
                    round_summary += summary
                else:
                    logger.error(f"Error in concurrent summarization: {summary}")
                    round_summary += "Error processing result\n"
        else:
            # Sequential summarization mode (original)
            for result in round_results:
                server = result.get('server', 'unknown')
                tool_name = result['tool']
                parameters = result.get('parameters', {})
                
                # Format parameters for display
                params_str = f"{parameters}" if parameters else "{}"
                
                if result['success']:
                    content = result['result']
                    token_count = self._estimate_token_count(content)
                    
                    if token_count <= config_loader.get_content_summary_threshold():
                        round_summary += f"Tool `{tool_name}` with Parameter {params_str} on {server} succeeded. Result: {content}\n"
                    else:
                        logger.info(f"Summarizing large result from {tool_name} ({token_count} tokens)")
                        try:
                            summarized_content = await self._summarize_content(content, "result")
                            round_summary += f"Tool `{tool_name}` with Parameter {params_str} on {server} succeeded. Result (summarized from {token_count} tokens): {summarized_content[:config_loader.get_content_truncate_length()]}\n"
                        except Exception as e:
                            logger.error(f"ERROR in summarizing result from {tool_name}: {e}")
                            import traceback
                            logger.error(f"Full traceback: {traceback.format_exc()}")
                            round_summary += f"Tool `{tool_name}` with Parameter {params_str} on {server} succeeded. Result (truncated): {content[:config_loader.get_content_truncate_length()]}...\n"
                else:
                    error_content = result['error']
                    token_count = self._estimate_token_count(error_content)
                    
                    if token_count <= config_loader.get_content_summary_threshold():
                        round_summary += f"Tool `{tool_name}` with Parameter {params_str} on {server} failed. Error: {error_content}\n"
                    else:
                        logger.info(f"Summarizing large error from {tool_name} ({token_count} tokens)")
                        try:
                            summarized_error = await self._summarize_content(error_content, "error")
                            round_summary += f"Tool `{tool_name}` with Parameter {params_str} on {server} failed. Error (summarized from {token_count} tokens): {summarized_error[:config_loader.get_error_truncate_length()]}\n"
                        except Exception as e:
                            logger.error(f"ERROR in summarizing error from {tool_name}: {e}")
                            import traceback
                            logger.error(f"Full traceback: {traceback.format_exc()}")
                            round_summary += f"Tool `{tool_name}` with Parameter {params_str} on {server} failed. Error (truncated): {error_content[:config_loader.get_error_truncate_length()]}...\n"
        
        self.accumulated_information += round_summary
        # Also update uncompressed version
        self.accumulated_information_uncompressed += round_summary
        logger.info(f"Round {round_num} finished. Total executions so far: {len(self.execution_results)}.")

    async def _synthesize_final_solution(self, task: str, total_executions: int) -> str:
        """LLM synthesizes a final, comprehensive solution from all execution results."""
        logger.info("Synthesizing final solution from all rounds...")

        prompt = f"""You are an expert solution synthesizer for multi-tool AI agent execution.
        ORIGINAL TASK: "{task}"
        A multi-round execution process has completed with {total_executions} total tool calls across multiple MCP servers.
        ACCUMULATED INFORMATION AND RESULTS:
        {self.accumulated_information}
        Based on the original task and all the information gathered from multiple servers, provide a final, comprehensive, and well-structured answer that directly addresses the user's request.
        Synthesize the key findings and present them in a clear, organized manner that shows how the different server capabilities were combined.
        """
        system_prompt = "You are an expert solution synthesizer specializing in multi-server AI agent results. Combine information from different servers into a cohesive, high-quality answer."

        # Simple retry with potential compression
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response_data = await self.llm.get_completion(
                    system_prompt, 
                    prompt, 
                    config_loader.get_planning_tokens(),
                    return_usage=True
                )
                
                # Handle both tuple and string returns
                if isinstance(response_data, tuple):
                    solution, usage = response_data
                    if usage:
                        self.total_output_tokens += usage.get('completion_tokens', 0)
                        self.total_prompt_tokens += usage.get('prompt_tokens', 0)
                        self.total_tokens += usage.get('total_tokens', 0)
                else:
                    solution = response_data
                
                return solution
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"ERROR in final solution attempt {attempt + 1}/{max_retries}: {e}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                
                # Try compression on token limit errors
                if self._is_token_limit_error(error_msg) and attempt < max_retries - 1:
                    logger.info("Token limit error in final solution, attempting compression...")
                    if await self.compress_accumulated_information():
                        # Regenerate prompt with compressed context
                        prompt = f"""You are an expert solution synthesizer for multi-tool AI agent execution.
                        ORIGINAL TASK: "{task}"
                        A multi-round execution process has completed with {total_executions} total tool calls across multiple MCP servers.
                        ACCUMULATED INFORMATION AND RESULTS:
                        {self.accumulated_information}
                        Based on the original task and all the information gathered from multiple servers, provide a final, comprehensive, and well-structured answer that directly addresses the user's request.
                        Synthesize the key findings and present them in a clear, organized manner that shows how the different server capabilities were combined.
                        """
                        continue
                
                # If this is the last attempt, re-raise the error
                if attempt == max_retries - 1:
                    raise e
        
        # Should not reach here
        return "Error: Failed to synthesize final solution"
        
    @staticmethod
    @handle_errors("extracting text from result", reraise=False)
    def _extract_text_from_result(result) -> str:
        """Extracts plain text from a CallToolResult object."""
        if hasattr(result, 'content') and result.content:
            return "".join(item.text for item in result.content if hasattr(item, 'text'))
        return str(result)
    
    @handle_errors("estimating token count", reraise=False)
    def _estimate_token_count(self, text: str) -> int:
        """Estimate token count using character-based approximation."""
        # Rough approximation: 1 token ≈ 4 characters for most languages
        return len(text) // 4
    
    @handle_errors("checking content filter error", reraise=False)
    def _is_content_filter_error(self, error_message: str) -> bool:
        """Check if the error is related to Azure content filtering."""
        error_lower = str(error_message).lower()
        content_filter_indicators = [
            "content management policy",
            "content filtering policies",
            "content_filter",
            "jailbreak",
            "responsibleaipolicyviolation"
        ]
        return any(indicator in error_lower for indicator in content_filter_indicators)
    
    @handle_errors("checking token limit error", reraise=False)
    def _is_token_limit_error(self, error_message: str) -> bool:
        """Check if the error is related to token limits."""
        error_lower = str(error_message).lower()
        token_limit_indicators = [
            "maximum context length",
            "context length",
            "token limit",
            "too many tokens",
            "exceeds maximum",
            "requested too many tokens"
        ]
        return any(indicator in error_lower for indicator in token_limit_indicators)

    @handle_errors("creating fallback LLM", reraise=False)
    async def _get_fallback_llm(self):
        """Get qwen3-32b as fallback LLM for content filtering issues."""
        from llm.factory import LLMFactory
        model_configs = LLMFactory.get_model_configs()
        
        # Try to get qwen3-32b model
        fallback_config = model_configs.get('qwen-3-32b')
        if not fallback_config:
            logger.warning("qwen-3-32b fallback model not available")
            return None
            
        fallback_llm = await LLMFactory.create_llm_provider(fallback_config)
        logger.info("Created qwen-3-32b fallback LLM for content summarization")
        return fallback_llm

    async def _summarize_content(self, content: str, content_type: str = "result") -> str:
        """Summarize content using LLM to keep it under threshold tokens."""
        system_prompt = f"You are a helpful assistant. I need your help to extract key information from content."
        
        user_prompt = f"""Summarize the following content to less than {config_loader.get_content_summary_threshold()} tokens while preserving all important information: CONTENT: {content} SUMMARIZED CONTENT:"""
        
        try:
            summary = await self.llm.get_completion(
                system_prompt, 
                user_prompt[:config_loader.get_user_prompt_max_length()], 
                config_loader.get_summarization_max_tokens()
            )
            return summary.strip()
            
        except Exception as e:
            logger.error(f"ERROR in primary model summarizing {content_type} content: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            # Check if this is a content filter error
            if self._is_content_filter_error(str(e)):
                logger.info("Content filter error detected, attempting fallback to qwen-3-32b")
                
                try:
                    fallback_llm = await self._get_fallback_llm()
                    if fallback_llm:
                        logger.info("Using qwen-3-32b fallback for content summarization")
                        summary = await fallback_llm.get_completion(
                            system_prompt, 
                            user_prompt[:config_loader.get_user_prompt_max_length()], 
                            3000
                        )
                        logger.info("Successfully summarized using fallback model")
                        return summary.strip()
                    else:
                        logger.warning("Fallback LLM not available")
                        
                except Exception as fallback_error:
                    logger.error(f"Fallback model also failed: {fallback_error}")
            
            # Final fallback: simple truncation
            logger.info(f"Using truncation fallback for {content_type} content")
            return content[:config_loader.get_content_summary_threshold()] + "... [truncated due to summarization failure]"
    
    @handle_errors("calculating tool token consumption", reraise=False)
    def _log_tools_token_stats(self):
        """Log token consumption statistics for tool descriptions and input schemas"""
        from mcp_modules.connector import MCPConnector
        
        # Calculate token consumption for all available tools
        stats = MCPConnector.estimate_tools_token_count(self.all_tools)
        
        logger.info("=== Tool Description Token Statistics ===")
        logger.info(f"Total tools: {stats['tool_count']}")
        logger.info(f"Total tokens: {stats['total_tokens']}")
        logger.info(f"Description tokens: {stats['description_tokens']}")
        logger.info(f"Schema tokens: {stats['schema_tokens']}")
        logger.info(f"Average tokens per tool: {stats['total_tokens'] // stats['tool_count'] if stats['tool_count'] > 0 else 0}")
        
        
        # Log top 5 tools with highest token consumption
        if stats['per_tool_tokens']:
            sorted_tools = sorted(
                stats['per_tool_tokens'].items(), 
                key=lambda x: x[1]['total'], 
                reverse=True
            )
            logger.info("=== Top 5 Tools by Token Consumption ===")
            for i, (tool_name, tool_stats) in enumerate(sorted_tools[:5], 1):
                logger.info(f"{i}. {tool_name}: {tool_stats['total']} tokens (description: {tool_stats['description']}, schema: {tool_stats['schema']})")
        
        logger.info("========================")
    
    @handle_errors("compressing accumulated information", reraise=False)
    async def compress_accumulated_information(self, target_tokens: int = 3000) -> bool:
        """
        Compress accumulated_information using LLM to reduce token usage
        
        Args:
            target_tokens: Target token count
            
        Returns:
            bool: Whether compression was successful
        """
        if not self.accumulated_information:
            logger.info("No accumulated information to compress")
            return False
        
        original_length = len(self.accumulated_information)
        original_tokens = original_length // 4
        
        if original_tokens <= target_tokens:
            logger.info(f"Accumulated information already within target ({original_tokens} <= {target_tokens} tokens)")
            return False
        
        logger.info(f"Starting LLM-based compression of accumulated_information: {original_tokens} tokens -> target {target_tokens} tokens")
        
        # Use LLM to compress the accumulated information intelligently
        system_prompt = "You are an expert information summarizer. Your task is to compress execution history while preserving all critical information and findings."
        
        user_prompt = f"""Please compress the following execution history to approximately {target_tokens} tokens while preserving:
        1. All key findings and results
        2. Important tool execution outcomes
        3. Critical information discovered
        4. Task progress and context
        EXECUTION HISTORY TO COMPRESS:
        {self.accumulated_information}
        COMPRESSED EXECUTION HISTORY:"""

        try:
            # Use LLM to compress - no context compression callback to avoid recursion
            compressed_content = await self.llm.get_completion(
                system_prompt, 
                user_prompt[:config_loader.get_user_prompt_max_length()],  # Limit input to prevent token issues
                target_tokens
            )
            
            # Validate compression result
            compressed_length = len(compressed_content)
            compressed_tokens = compressed_length // 4
            
            if compressed_tokens < original_tokens:
                self.accumulated_information = compressed_content.strip()
                logger.info(f"LLM compression successful: {original_tokens} -> {compressed_tokens} tokens ({((original_tokens - compressed_tokens) / original_tokens * 100):.1f}% reduction)")
                return True
            else:
                logger.warning("LLM compression did not reduce token count, falling back to rule-based compression")
                # Fall back to rule-based compression
                return self._fallback_rule_based_compression(target_tokens, original_tokens)
                
        except Exception as llm_error:
            logger.warning(f"LLM compression failed: {llm_error}, falling back to rule-based compression")
            return self._fallback_rule_based_compression(target_tokens, original_tokens)
    
    @handle_errors("rule-based compression fallback", reraise=False)
    def _fallback_rule_based_compression(self, target_tokens: int, original_tokens: int) -> bool:
        """Fallback rule-based compression when LLM compression fails"""
        rounds = self.accumulated_information.split("--- Summary of Round ")
        
        if len(rounds) <= 1:
            # Simple truncation compression
            target_chars = target_tokens * 4
            compressed_info = f"[Early execution history compressed for token limit]\n\n{self.accumulated_information[-target_chars:]}"
            self.accumulated_information = compressed_info
            
            new_length = len(self.accumulated_information)
            new_tokens = new_length // 4
            logger.info(f"Rule-based simple compression completed: {original_tokens} -> {new_tokens} tokens")
            return True
        
        # Smart round-based compression
        first_part = rounds[0]
        keep_recent_rounds = 2
        recent_rounds = rounds[-keep_recent_rounds:] if len(rounds) > keep_recent_rounds else rounds[1:]
        
        middle_rounds_count = len(rounds) - 1 - len(recent_rounds)
        if middle_rounds_count > 0:
            compressed_middle = f"[Rounds 2-{middle_rounds_count+1} compressed: Multiple tools executed successfully, information gathered and accumulated]"
        else:
            compressed_middle = ""
        
        compressed_parts = [first_part.strip()]
        if compressed_middle:
            compressed_parts.append(compressed_middle)
        
        for round_content in recent_rounds:
            if round_content.strip():
                compressed_parts.append("--- Summary of Round " + round_content)
        
        self.accumulated_information = "\n\n".join(compressed_parts)
        
        new_length = len(self.accumulated_information)
        new_tokens = new_length // 4
        
        # Further compression if still too long
        if new_tokens > target_tokens:
            target_chars = target_tokens * 4
            if len(self.accumulated_information) > target_chars:
                keep_start = target_chars // 2
                keep_end = target_chars // 2
                start_part = self.accumulated_information[:keep_start]
                end_part = self.accumulated_information[-keep_end:]
                self.accumulated_information = f"{start_part}\n\n[Middle content compressed for token limit]\n\n{end_part}"
                
                new_length = len(self.accumulated_information)
                new_tokens = new_length // 4
        
        logger.info(f"Rule-based compression completed: {original_tokens} -> {new_tokens} tokens ({((original_tokens - new_tokens) / original_tokens * 100):.1f}% reduction)")
        return True

