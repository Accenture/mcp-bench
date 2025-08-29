"""
Task Evaluation System for MCP-Bench

This module provides comprehensive evaluation capabilities for MCP task execution,
including execution compliance analysis, LLM performance assessment, and tool accuracy metrics.
"""

import asyncio
import logging
import random
import time
from typing import List, Dict, Any, Optional, Protocol
from collections import Counter
from abc import ABC, abstractmethod
import jsonschema
from jsonschema import ValidationError
import config.config_loader as config_loader

logger = logging.getLogger(__name__)

def safe_get(item, key, default=None):
    """Safely get a value from a dictionary"""
    if isinstance(item, dict):
        return item.get(key, default)
    else:
        return default
class LLMProvider(Protocol):
    """Protocol for LLM providers used in evaluation"""
    async def get_completion(self, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
        ...
    
    def clean_and_parse_json(self, raw_json: str) -> Any:
        ...
class BaseEvaluator(ABC):
    """Abstract base class for task evaluators.
    
    Provides the interface for all evaluation implementations.
    
    Attributes:
        llm: LLM provider for evaluation tasks
    """
    
    def __init__(self, llm_provider: LLMProvider) -> None:
        """Initialize the evaluator.
        
        Args:
            llm_provider: LLM provider for evaluation tasks
        """
        self.llm = llm_provider
    
    @abstractmethod
    async def evaluate(self, task: str, execution_results: List[Dict[str, Any]], 
                      final_solution: str, total_rounds: int, available_tools: Dict[str, Any],
                      **kwargs) -> Optional[Dict[str, Any]]:
        """Evaluate task execution and return metrics"""
        pass
class LLMJudge:
    """Handles LLM-based evaluation of task performance.
    
    Uses LLM to evaluate task completion quality, tool usage,
    and planning effectiveness.
    
    Attributes:
        llm: LLM provider for evaluation
        enable_judge_stability: Whether to enable stability testing
        evaluation_dimensions: Dictionary of evaluation criteria
    """
    
    def __init__(
        self,
        llm_provider: LLMProvider,
        enable_judge_stability: bool = False
    ) -> None:
        """Initialize the LLM judge.
        
        Args:
            llm_provider: LLM provider for evaluation
            enable_judge_stability: Whether to enable judge stability testing
        """
        self.llm = llm_provider
        self.enable_judge_stability = enable_judge_stability
        
        # Structured evaluation criteria for randomization (6 dimensions)
        self.evaluation_dimensions = {
            "Task Completion": {
                "Task Fulfillment": {
                    "1-3": "Perfectly completes 10-30% of requirements.",
                    "4-6": "Perfectly completes 40-60% of requirements.",
                    "7-8": "Perfectly completes 70-80% of requirements.",
                    "9-10": "Perfectly completes 90-100% of requirements."
                },
                "Grounding": {
                    "1-3": "10-30% of claims are perfectly grounded in tool outputs.",
                    "4-6": "40-60% of claims are perfectly grounded in tool outputs.",
                    "7-8": "70-80% of claims are perfectly grounded in tool outputs.",
                    "9-10": "90-100% of claims are perfectly grounded in tool outputs."
                }
            },
            "Tool Usage": {
                "Tool Appropriateness": {
                    "1-3": "10-30% of tools were perfectly selected for their subtasks.",
                    "4-6": "40-60% of tools were perfectly selected for their subtasks.",
                    "7-8": "70-80% of tools were perfectly selected for their subtasks.",
                    "9-10": "90-100% of tools were perfectly selected for their subtasks."
                },
                "Parameter Accuracy": {
                    "1-3": "10-30% of tool calls have perfectly accurate and complete parameters.",
                    "4-6": "40-60% of tool calls have perfectly accurate and complete parameters.",
                    "7-8": "70-80% of tool calls have perfectly accurate and complete parameters.",
                    "9-10": "90-100% of tool calls have perfectly accurate and complete parameters."
                }
            },
            "Planning Effectiveness and Efficiency": {
                "Dependency Awareness": {
                    "1-3": "10-30% of dependency chains are perfectly executed.",
                    "4-6": "40-60% of dependency chains are perfectly executed.",
                    "7-8": "70-80% of dependency chains are perfectly executed.",
                    "9-10": "90-100% of dependency chains are perfectly executed."
                },
                "Parallelism and Efficiency": {
                    "1-3": "More than 70% redundant calls OR less than 30% of parallelizable tasks were executed in parallel.",
                    "4-6": "40-60% redundant calls OR 40-60% of parallelizable tasks were executed in parallel.",
                    "7-8": "20-30% redundant calls AND 70-80% of parallelizable tasks were executed in parallel.",
                    "9-10": "Less than 10% redundant calls AND 90-100% of parallelizable tasks were executed in parallel."
                }
            }
        }
    
    def _generate_randomized_prompt(self, task: str, final_solution: str, 
                                  execution_summary: str, total_rounds: int, 
                                  available_tools: Dict[str, Any] = None,
                                  concrete_task_description: str = None,
                                  dependency_analysis: str = None) -> str:
        """Generate evaluation prompt with randomized structure"""
        
        # Create copies for randomization without modifying originals
        dimensions_copy = {}
        for main_dim, sub_dims in self.evaluation_dimensions.items():
            dimensions_copy[main_dim] = {}
            for sub_dim, criteria in sub_dims.items():
                dimensions_copy[main_dim][sub_dim] = dict(criteria)
        
        # Randomize the order of main dimensions
        main_dimension_names = list(dimensions_copy.keys())
        random.shuffle(main_dimension_names)
        
        # Build the prompt with randomized structure
        prompt_parts = []
        
        # Header
        prompt_parts.append(f"""You are an impartial evaluator judging the quality of an AI agent's multi-server tool-based task execution.

            You must assign scores **only based on evidence** from the task, solution, and tool usage. Your evaluation should be:
            - Objective (avoid being influenced by language fluency or formatting)
            - Justified (include specific reasons tied to each score)
            - Robust against bias (ignore narrative style, verbosity, or formatting polish)

            ---""")

        # Task description section (with or without concrete reference)
        if concrete_task_description:
            prompt_parts.append(f"""
                **TASK PRESENTED TO AGENT**: "{task}"

                **CONCRETE TASK REFERENCE (For evaluation context only)**: 
                Note: The agent did NOT see this concrete version. It only saw the task above. 
                The task visible for the agent is the fuzzy version of the concrete task.
                The agent's interpretation of the fuzzy task may differ but still be valid.
                "{concrete_task_description}"
                """)
        else:
            prompt_parts.append(f'**ORIGINAL TASK**: "{task}"')

        # Add dependency analysis if available
        if dependency_analysis:
            prompt_parts.append(f"""
                **DEPENDENCY ANALYSIS**:
                Note: This analysis was generated during task creation to help understand tool dependencies.
                The agent did NOT see this analysis. It is provided as reference for evaluation purposes.
                {dependency_analysis}
                """)

        prompt_parts.append(f"""
            **FINAL SOLUTION**: "{final_solution}"
            **TOTAL ROUNDS**: {total_rounds}
            **EXECUTION SUMMARY**:
            {execution_summary}

            **AVAILABLE TOOLS** ({len(available_tools) if available_tools else 0} tools):
            {self._format_available_tools(available_tools)}

            ---""")
        
        # Add randomized dimension sections
        for main_dim in main_dimension_names:
            sub_dims = dimensions_copy[main_dim]
            
            # Randomize sub-dimension order
            sub_dim_names = list(sub_dims.keys())
            random.shuffle(sub_dim_names)
            
            prompt_parts.append(f"\n### {main_dim} Rubric (1–10 per subdimension)\n")
            
            for i, sub_dim in enumerate(sub_dim_names, 1):
                criteria = sub_dims[sub_dim]
                
                # Randomize criteria order within each sub-dimension
                criteria_items = list(criteria.items())
                random.shuffle(criteria_items)
                
                prompt_parts.append(f"{i}. **{sub_dim}**")
                for range_key, description in criteria_items:
                    prompt_parts.append(f"   - {range_key}: {description}")
                prompt_parts.append("")
        
        # Add bias mitigation and strict scoring guidelines
        prompt_parts.extend([
            "---",
            "",
            "### PERCENTAGE-BASED SCORING SYSTEM:",
            "",
            "**How to Calculate Scores:**",
            "For each dimension, calculate the DEFECT RATE:",
            "- Defect Rate = (Number of Issues / Total Opportunities) × 100%",
            "",
            "Then map defect rate to score:",
            "- 0-10% defects → Score 9-10 (Excellent to Perfect)",
            "- 10-30% defects → Score 7-9 (Good performance)",
            "- 30-50% defects → Score 5-7 (Average performance)",
            "- 50-70% defects → Score 3-5 (Poor performance)",
            "- 70-100% defects → Score 0-3 (Failed)",
            "",
            "**How to Score:**",
            "1. When evaluating percentages, be EXTREMELY STRICT about what counts as 'perfectly executed'",
            "2. 'Perfectly' means ALL of the following must be true:",
            "   - Correct tool selection (not just 'works' but OPTIMAL choice)",
            "   - Complete and accurate parameters (not just valid, but IDEAL)",
            "   - Zero redundancy (no repeated or unnecessary calls)",
            "   - Proper error handling (graceful recovery from ANY failure)",
            "   - Efficient execution (parallel when possible, minimal rounds)",
            "   - Concise output (no verbose explanations unless requested)",
            "3. If ANY of the above is missing, that portion is NOT perfectly executed (counts as 0%)",
            "4. Example: Task completed correctly but with 1 redundant call = that portion is 0% perfect",
            "",
            "**KEY PRINCIPLES:**",
            "1. ALWAYS calculate as percentage, NOT absolute numbers",
            "2. 10 errors in 100 calls (10%) = same score as 1 error in 10 calls (10%)",
            "3. Consider the OPPORTUNITY COUNT for each dimension:",
            "   - Tool calls: How many total calls were made?",
            "   - Parallelization: How many tasks COULD have been parallel?",
            "   - Parameters: How many total parameters across all calls?",
            "   - Claims: How many factual statements were made?",
            "   - Dependencies: How many dependency relationships exist?",
            "4. NORMALIZE by complexity - don't punish complex tasks:",
            "   - Simple task: 1 error/5 steps (20% defect) = Score 7",
            "   - Complex task: 4 errors/20 steps (20% defect) = Score 7",
            "",
            "---",
            "",
            "CRITICAL: Apply the STRICTEST interpretation of 'perfectly executed'. If there's ANY doubt, score lower.",
            "",
            "**CONCRETE SCORING EXAMPLES WITH PROPORTIONS:**",
            "",
            "Task Fulfillment:",
            "- Completed 19/20 requirements (5% defect rate) = Score 9",
            "- Completed 16/20 requirements (20% defect rate) = Score 8",
            "- Completed 12/20 requirements (40% defect rate) = Score 6",
            "- Completed 8/20 requirements (60% defect rate) = Score 4",
            "",
            "Tool Appropriateness:",
            "- 19/20 tools optimal (5% defect rate) = Score 9",
            "- 16/20 tools optimal (20% defect rate) = Score 8",
            "- 12/20 tools optimal (40% defect rate) = Score 6",
            "- 8/20 tools optimal (60% defect rate) = Score 4",
            "",
            "Parallelism & Efficiency:",
            "- 9/10 parallelizable tasks done in parallel (10% missed) = Score 9",
            "- 8/10 parallelizable tasks done in parallel (20% missed) = Score 8",
            "- 6/10 parallelizable tasks done in parallel (40% missed) = Score 6",
            "- 4/10 parallelizable tasks done in parallel (60% missed) = Score 4",
            "",
            "Grounding:",
            "- 19/20 claims supported by evidence (5% unsupported) = Score 9",
            "- 16/20 claims supported by evidence (20% unsupported) = Score 8",
            "- 12/20 claims supported by evidence (40% unsupported) = Score 6",
            "- 8/20 claims supported by evidence (60% unsupported) = Score 4",
            "",
            "Parameter Accuracy:",
            "- 95/100 parameters perfect (5% defect rate) = Score 9",
            "- 80/100 parameters perfect (20% defect rate) = Score 8",
            "- 60/100 parameters perfect (40% defect rate) = Score 6",
            "- 40/100 parameters perfect (60% defect rate) = Score 4",
            "",
            "FORMAT NOTE: Text output when JSON not required = NO PENALTY (0% defect)",
            "FORMAT NOTE: Missing JSON when explicitly required = Count as failed requirement",
            "",
            "Remember: Most real-world executions should score 4-6. Scores of 8+ should be EXCEPTIONAL.",
            "",
            "FINAL REMINDER BEFORE SCORING:",
            "- Default to 4-5 unless you have strong evidence for higher",
            "- Count ONLY truly perfect executions toward the percentage",
            "- Be your most critical self - find flaws first, then acknowledge successes",
            "- If you're considering a score above 7, re-examine for ANY imperfection",
            "- Server count is IRRELEVANT - using more servers is NOT better",
            "",
            "---",
            "",
            "CRITICAL EVALUATION REQUIREMENTS:",
            "1. You MUST map each score to the exact percentage ranges in the rubrics.",
            "2. Task Completion and Tool Usage MUST be evaluated against the CONCRETE TASK REFERENCE, not the fuzzy task.",
            "3. Planning Effectiveness should be evaluated based on the PROPORTION of dependencies correctly handled, not the absolute number of steps executed or exact conformance to the dependency analysis.",
            "4. First calculate the actual percentage of completion/success, then assign the corresponding score range.",
            "5. IMPORTANT: Focus on completion RATIOS not absolute numbers - completing 7/10 steps (70%) should score similarly to completing 14/20 steps (70%), regardless of task complexity.",
            "",
            "Please score based on COMPLETION PERCENTAGES and PROPORTIONAL SUCCESS, not absolute numbers of tools called or steps executed. Return your evaluation scoring and reasoning in this exact JSON format:",
            "{",
            "",
            '  "task_fulfillment_reasoning": "Explain how well the agent fulfilled the detailed task objectives, referencing specific content from the CONCRETE TASK DESCRIPTION and what percentage was completed.",',
            '  "grounding_reasoning": "Explain how well the agent\'s outputs were grounded in actual tool results versus unsupported claims.",',
            '  "tool_appropriateness_reasoning": "Explain whether the tools selected were appropriate for each subtask requirement.",',
            '  "parameter_accuracy_reasoning": "Explain the accuracy and completeness of parameters used in tool calls, noting any missing required parameters or incorrect values.",',
            '  "dependency_awareness_reasoning": "Explain how well the agent understood and respected task dependencies (what percentage of dependencies were handled correctly), refer to the provided dependency analysis section.",',
            '  "parallelism_efficiency_reasoning": "Explain the efficiency of execution, including use of parallelism and avoiding redundancy, refer to the provided dependency analysis section.",',
            "",
            '  "task_fulfillment": X,',
            '  "grounding": X,',
            "",
            '  "tool_appropriateness": X,',
            '  "parameter_accuracy": X,',
            "",
            '  "dependency_awareness": X,',
            '  "parallelism_and_efficiency": X,',
            "",
            "}",
            "",
            "Return **only** the JSON object."
        ])
        
        return "\n".join(prompt_parts)

    def _calculate_average_scores(self, all_scores: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate average scores from multiple evaluations"""
        if not all_scores:
            raise ValueError("No scores to average")
        
        # Define the 6 score fields
        score_fields = [
            "task_fulfillment", "grounding",
            "tool_appropriateness", "parameter_accuracy", 
            "dependency_awareness", "parallelism_and_efficiency"
        ]
        
        # Define analysis text fields to preserve from first evaluation
        analysis_fields = [
            "task_completion_analysis",
            "tool_selection_analysis",
            "planning_effectiveness_and_efficiency_analysis"
        ]
        
        # Calculate averages for each score field
        averaged_result = {}
        
        # Copy non-score fields from first result (including analysis texts)
        first_result = all_scores[0]
        for key in first_result:
            if key not in score_fields:
                averaged_result[key] = first_result[key]
        
        # Ensure analysis fields are preserved even if missing
        for field in analysis_fields:
            if field not in averaged_result and field in first_result:
                averaged_result[field] = first_result[field]
        
        # Calculate average scores
        for field in score_fields:
            valid_scores = []
            for result in all_scores:
                if field in result and isinstance(result[field], (int, float)):
                    valid_scores.append(result[field])
            
            if valid_scores:
                averaged_result[field] = sum(valid_scores) / len(valid_scores)
            else:
                logger.warning(f"No valid scores found for {field}, using 0")
                averaged_result[field] = 0
        
        # Recalculate aggregate scores from averaged subdimension scores
        task_completion_scores = [
            averaged_result['task_fulfillment'], 
            averaged_result['grounding']
        ]
        tool_selection_scores = [
            averaged_result['tool_appropriateness'], 
            averaged_result['parameter_accuracy']
        ]
        planning_scores = [
            averaged_result['dependency_awareness'], 
            averaged_result['parallelism_and_efficiency']
        ]
        
        # Calculate aggregate scores
        averaged_result['task_completion_score'] = sum(task_completion_scores) / len(task_completion_scores)
        averaged_result['tool_selection_score'] = sum(tool_selection_scores) / len(tool_selection_scores)
        averaged_result['planning_effectiveness_and_efficiency_score'] = sum(planning_scores) / len(planning_scores)
        
        # Note: Removed flat_average_score calculation as it's no longer needed
        
        logger.info(f"Averaged scores from {len(all_scores)} stability evaluations, preserving reasoning from first evaluation")
        return averaged_result
    
    def _format_available_tools(self, available_tools: Dict[str, Any]) -> str:
        """Format available tools with descriptions for display in evaluation prompt"""
        if not available_tools:
            return "No tools available"
        
        # Group tools by server with descriptions
        servers = {}
        for tool_name, tool_info in available_tools.items():
            server = tool_info.get('server', 'Unknown')
            if server not in servers:
                servers[server] = []
            
            # Get tool description, truncate if too long
            description = tool_info.get('description', 'No description available')
            if description is None:
                description = 'No description available'
            if len(description) > 500:
                description = description[:500] + "..."
            
            servers[server].append({
                'name': tool_name,
                'description': description
            })
        
        # Format output with ALL tools and descriptions
        lines = []
        for server, tools in sorted(servers.items()):
            lines.append(f"[{server}] ({len(tools)} tools)")
            
            # Show ALL tools with descriptions for each server
            for tool in tools:
                lines.append(f"  - {tool['name']}: {tool['description']}")
            
            lines.append("")  # Empty line between servers
        
        return '\n'.join(lines).strip() if lines else "No tools available"

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
    
    async def compress_for_judge(self, accumulated_info: str, target_tokens: int = 10000) -> str:
        """Compress execution history specifically for judge evaluation.
        
        This compression preserves more detail than agent compression,
        focusing on evidence needed for accurate evaluation.
        
        Args:
            accumulated_info: The execution history to compress
            target_tokens: Target token count (default 10000 for judge)
            
        Returns:
            Compressed execution history optimized for evaluation
        """
        if not accumulated_info:
            return ""
            
        # Estimate current tokens
        current_tokens = len(accumulated_info) // 4
        if current_tokens <= target_tokens:
            return accumulated_info
            
        logger.info(f"Compressing execution history for judge: {current_tokens} -> {target_tokens} tokens")
        
        system_prompt = """You are compressing execution history for a judge model that needs to evaluate agent performance. Focus on preserving evidence of task completion and decision quality."""
        
        user_prompt = f"""Compress the following agent execution history for evaluation purposes.

            CRITICAL REQUIREMENTS FOR JUDGE COMPRESSION:
            1. Preserve ALL tool calls with their exact parameters and server names
            2. Keep key results and error messages that show task progress
            3. Maintain the chronological sequence of execution rounds
            4. Retain evidence of success/failure for each operation
            5. Keep decision reasoning that shows agent's problem-solving approach
            6. Preserve numerical results, data values, and specific findings
            7. Keep any information that proves task completion or failure

            Target length: approximately {target_tokens} tokens

            EXECUTION HISTORY TO COMPRESS:
            {accumulated_info}

            COMPRESSED VERSION FOR EVALUATION:"""
        
        try:
            compressed = await self.llm.get_completion(
                system_prompt,
                user_prompt,
                target_tokens
            )
            
            compressed_tokens = len(compressed) // 4
            logger.info(f"Judge compression successful: {current_tokens} -> {compressed_tokens} tokens")
            return compressed.strip()
            
        except Exception as e:
            logger.error(f"Failed to compress for judge: {e}")
            # Fallback to simple truncation if compression fails
            target_chars = target_tokens * 4
            if len(accumulated_info) > target_chars:
                return accumulated_info[:target_chars] + "\n[Truncated for token limit]"
            return accumulated_info

    async def evaluate_task_performance(self, task: str, final_solution: str, 
                                      execution_results: List[Dict[str, Any]], 
                                      total_rounds: int, available_tools: Dict[str, Any],
                                      accumulated_information: str = None,
                                      concrete_task_description: str = None,
                                      dependency_analysis: str = None) -> Dict[str, Any]:
        """Evaluate task performance using LLM judge with 10-dimension scoring"""
        
        # Track the accumulated information to use (may be compressed if needed)
        accumulated_info_to_use = accumulated_information
        
        # Retry loop for handling token limit errors
        max_retries = 2
        for retry_attempt in range(max_retries):
            try:
                # Prepare execution summary with accumulated information
                execution_summary = self._create_execution_summary(execution_results, total_rounds, accumulated_info_to_use)
                
                # Perform the actual evaluation
                return await self._perform_evaluation(
                    task, final_solution, execution_summary, total_rounds, 
                    available_tools, concrete_task_description, dependency_analysis
                )
                
            except Exception as e:
                error_msg = str(e)
                
                # Check if it's a token limit error and we haven't compressed yet
                if self._is_token_limit_error(error_msg) and retry_attempt == 0 and accumulated_information:
                    logger.info("Token limit error in judge evaluation, compressing execution history to 10000 tokens...")
                    
                    # Compress the accumulated information for judge
                    accumulated_info_to_use = await self.compress_for_judge(accumulated_information, target_tokens=10000)
                    logger.info("Retrying evaluation with compressed execution history...")
                    continue
                    
                # If not a token limit error or already tried compression, re-raise
                logger.error(f"Error in judge evaluation: {e}")
                raise
        
        # Should not reach here
        raise Exception("Unexpected evaluation flow")
    
    async def _perform_evaluation(self, task: str, final_solution: str, 
                                 execution_summary: str, total_rounds: int, 
                                 available_tools: Dict[str, Any],
                                 concrete_task_description: str = None,
                                 dependency_analysis: str = None) -> Dict[str, Any]:
        """Perform the actual evaluation (extracted for retry logic)"""
        
        if self.enable_judge_stability:
            # Run 5 evaluations with randomized prompt structure
            stability_start_time = time.time()
            logger.info("Running LLM Judge stability testing (5 randomized evaluations)")
            all_scores = []
            individual_times = []
            
            for i in range(5):
                eval_start_time = time.time()
                logger.debug(f"Running stability evaluation {i+1}/5")
                
                # Generate randomized prompt for this iteration
                randomized_prompt = self._generate_randomized_prompt(
                    task, final_solution, execution_summary, total_rounds, available_tools,
                    concrete_task_description, dependency_analysis
                )
                
                try:
                    llm_start_time = time.time()
                    response = await self.llm.get_completion(
                        "You are an expert AI task execution evaluator. Score each dimension objectively based on evidence.", 
                        randomized_prompt, 
                        config_loader.get_evaluation_max_tokens()
                    )
                    llm_end_time = time.time()
                    
                    parse_start_time = time.time()
                    parsed_scores = self.llm.clean_and_parse_json(response)
                    parse_end_time = time.time()
                    
                    all_scores.append(parsed_scores)
                    
                    eval_total_time = time.time() - eval_start_time
                    llm_time = llm_end_time - llm_start_time
                    parse_time = parse_end_time - parse_start_time
                    individual_times.append({
                        'total': eval_total_time,
                        'llm_call': llm_time,
                        'parsing': parse_time
                    })
                    
                    logger.debug(f"Evaluation {i+1}/5 completed in {eval_total_time:.2f}s (LLM: {llm_time:.2f}s, Parse: {parse_time:.3f}s)")
                    
                except Exception as e:
                    logger.warning(f"Stability evaluation {i+1}/5 failed: {e}")
                    import traceback
                    logger.debug(f"Full traceback: {traceback.format_exc()}")
                    continue
            
            if not all_scores:
                raise RuntimeError("All stability evaluations failed")
            
            # Calculate average scores
            stability_total_time = time.time() - stability_start_time
            avg_times = {
                'total': sum(t['total'] for t in individual_times) / len(individual_times),
                'llm_call': sum(t['llm_call'] for t in individual_times) / len(individual_times),
                'parsing': sum(t['parsing'] for t in individual_times) / len(individual_times)
            }
            
            logger.info(f"LLM Judge Pipeline Runtime:")
            logger.info(f"   Total judge pipeline time: {stability_total_time:.2f}s")
            logger.info(f"   Average per evaluation: {avg_times['total']:.2f}s")
            logger.info(f"   Average LLM call time: {avg_times['llm_call']:.2f}s")
            logger.info(f"   Average parsing time: {avg_times['parsing']:.3f}s")
            logger.info(f"   Completed {len(all_scores)}/5 evaluations successfully")
            
            return self._calculate_average_scores(all_scores)
        
        # Standard single evaluation (original behavior)
        # Task description section (with or without concrete reference)
        if concrete_task_description:
            task_section = f"""
                **TASK PRESENTED TO AGENT**: "{task}"

                **CONCRETE TASK REFERENCE (For evaluation context only)**: 
                Note: The agent did NOT see this concrete version. It only saw the task above.
                The task visible for the agent is the fuzzy version of the concrete task.
                This reference helps assess actual task completion but is not the sole criterion.
                The agent's interpretation of the fuzzy task may differ but still be valid.
                
                FORMAT REMINDER: If the concrete task mentions JSON but the TASK PRESENTED TO AGENT doesn't explicitly require it, 
                DO NOT penalize for not using JSON format. Only the task presented to agent's requirements matter for format.
                "{concrete_task_description}"
                """
        else:
            task_section = f'**ORIGINAL TASK**: "{task}"'
        
        # Add dependency analysis section if available
        dependency_section = ""
        if dependency_analysis:
            dependency_section = f"""
            **DEPENDENCY ANALYSIS (Reference Only)**:
            Note: This analysis was generated during task creation to help understand tool dependencies.
            The agent did NOT see this analysis. It is provided as reference for evaluation purposes.
            {dependency_analysis}
            """

        prompt = f"""You are a STRICT evaluator. Your role is to critically assess performance with HIGH STANDARDS.

            IMPORTANT: The average score across all evaluations should be around 4-5, NOT 7-8.
            
            You must assign scores **only based on evidence** from the task, solution, and tool usage. Your evaluation should be:
            - Extremely Critical (assume mediocre performance unless proven otherwise)
            - Evidence-based (require strong proof for scores above 5)
            - Conservative (when in doubt, score lower - aim for 4-5 average)
            
            CRITICAL FORMAT RULES:
            - DO NOT penalize for output format (JSON, text, etc.) unless the TASK PRESENTED TO AGENT explicitly requires it
            - If the task presented to agent says "provide information" without specifying format, ANY readable format is acceptable
            - Only deduct points for format if the task explicitly states "return as JSON" or "format as table" etc.
            - Focus on CONTENT correctness, not presentation style
            
            ---
            
            **AVAILABLE TOOLS** ({len(available_tools) if available_tools else 0} tools):
            {self._format_available_tools(available_tools)}
            {task_section}
            **EXECUTION SUMMARY**:
            {execution_summary}
            **FINAL SOLUTION**: "{final_solution}"
            **TOTAL ROUNDS**: {total_rounds}

            {dependency_section}
            
            ---
            
            ### Task Completion Rubric (1–10 per subdimension)
            
            1. **Task Fulfillment and Quality**
            - 1–3: Perfectly completes 10-30% of requirements.
            - 4–6: Perfectly completes 40-60% of requirements.
            - 7–8: Perfectly completes 70-80% of requirements.
            - 9–10: Perfectly completes 90-100% of requirements.
            NOTE: Requirements come from the task present to agent only. Format (JSON/text) is NOT a requirement unless explicitly stated in the task present to agent.
            
            3. **Grounding**
            - 1–3: 10-30% of claims are perfectly grounded in tool outputs.
            - 4–6: 40-60% of claims are perfectly grounded in tool outputs.
            - 7–8: 70-80% of claims are perfectly grounded in tool outputs.
            - 9–10: 90-100% of claims are perfectly grounded in tool outputs.

            ---
            
            ### Tool Usage Rubric (1–10 per subdimension)
            
            1. **Tool Appropriateness**
            - 1–3: 10-30% of tools were perfectly selected for their subtasks.
            - 4–6: 40-60% of tools were perfectly selected for their subtasks.
            - 7–8: 70-80% of tools were perfectly selected for their subtasks.
            - 9–10: 90-100% of tools were perfectly selected for their subtasks.
            
            3. **Parameter Accuracy**
            - 1–3: 10-30% of tool calls have perfectly accurate and complete parameters.
            - 4–6: 40-60% of tool calls have perfectly accurate and complete parameters.
            - 7–8: 70-80% of tool calls have perfectly accurate and complete parameters.
            - 9–10: 90-100% of tool calls have perfectly accurate and complete parameters.
            
            ---
            
            ### Planning Effectiveness and Efficiency (1–10 per subdimension)

            2. **Dependency Awareness**
            - 1–3: 10-30% of dependency chains are perfectly executed.
            - 4–6: 40-60% of dependency chains are perfectly executed.
            - 7–8: 70-80% of dependency chains are perfectly executed.
            - 9–10: 90-100% of dependency chains are perfectly executed.

            3. **Parallelism and Efficiency**
            - 1–3: More than 70% redundant calls OR less than 30% of parallelizable tasks were executed in parallel.
            - 4–6: 40-60% redundant calls OR 40-60% of parallelizable tasks were executed in parallel.
            - 7–8: 20-30% redundant calls AND 70-80% of parallelizable tasks were executed in parallel.
            - 9–10: Less than 10% redundant calls AND 90-100% of parallelizable tasks were executed in parallel.
            ---
            
            ### PERCENTAGE-BASED SCORING SYSTEM:
            
            **How to Calculate Scores:**
            For each dimension, calculate the DEFECT RATE:
            - Defect Rate = (Number of Issues / Total Opportunities) × 100%
            
            Then map defect rate to score:
            - 0-10% defects → Score 9-10 (Excellent to Perfect)
            - 10-30% defects → Score 7-9 (Good performance)
            - 30-50% defects → Score 5-7 (Average performance)
            - 50-70% defects → Score 3-5 (Poor performance)
            - 70-100% defects → Score 0-3 (Failed)
            
            **How to Score:**
            1. When evaluating percentages, be EXTREMELY STRICT about what counts as "perfectly executed"
            2. "Perfectly" means ALL of the following must be true:
               - Correct tool selection (not just "works" but OPTIMAL choice)
               - Complete and accurate parameters (not just valid, but IDEAL)
               - Zero redundancy (no repeated or unnecessary calls)
               - Proper error handling (graceful recovery from ANY failure)
               - Efficient execution (parallel when possible, minimal rounds)
               - Concise output (no verbose explanations unless requested)
            3. If ANY of the above is missing, that portion is NOT perfectly executed (counts as 0%)
            4. Example: Task completed correctly but with 1 redundant call = that portion is 0% perfect
            
            **KEY PRINCIPLES:**
            1. ALWAYS calculate as percentage, NOT absolute numbers
            2. 10 errors in 100 calls (10%) = same score as 1 error in 10 calls (10%)
            3. Consider the OPPORTUNITY COUNT for each dimension:
               - Tool calls: How many total calls were made?
               - Parallelization: How many tasks COULD have been parallel?
               - Parameters: How many total parameters across all calls?
               - Claims: How many factual statements were made?
               - Dependencies: How many dependency relationships exist?
            ---
            
            CRITICAL: Apply the STRICTEST interpretation of "perfectly executed". If there's ANY doubt, score lower.
            
            **CONCRETE SCORING EXAMPLES WITH PROPORTIONS:**
            
            Task Fulfillment:
            - Completed 19/20 requirements (5% defect rate) = Score 9
            - Completed 16/20 requirements (20% defect rate) = Score 8
            - Completed 12/20 requirements (40% defect rate) = Score 6
            - Completed 8/20 requirements (60% defect rate) = Score 4
            
            Tool Appropriateness:
            - 19/20 tools optimal (5% defect rate) = Score 9
            - 16/20 tools optimal (20% defect rate) = Score 8
            - 12/20 tools optimal (40% defect rate) = Score 6
            - 8/20 tools optimal (60% defect rate) = Score 4
            
            Parallelism & Efficiency:
            - 9/10 parallelizable tasks done in parallel (10% missed) = Score 9
            - 8/10 parallelizable tasks done in parallel (20% missed) = Score 8
            - 6/10 parallelizable tasks done in parallel (40% missed) = Score 6
            - 4/10 parallelizable tasks done in parallel (60% missed) = Score 4
            
            Grounding:
            - 19/20 claims supported by evidence (5% unsupported) = Score 9
            - 16/20 claims supported by evidence (20% unsupported) = Score 8
            - 12/20 claims supported by evidence (40% unsupported) = Score 6
            - 8/20 claims supported by evidence (60% unsupported) = Score 4
            
            Parameter Accuracy:
            - 95/100 parameters perfect (5% defect rate) = Score 9
            - 80/100 parameters perfect (20% defect rate) = Score 8
            - 60/100 parameters perfect (40% defect rate) = Score 6
            - 40/100 parameters perfect (60% defect rate) = Score 4
            
            FORMAT NOTE: Text output when JSON not required in the task present to the agent = NO PENALTY (0% defect)
            FORMAT NOTE: Missing JSON when explicitly required in the task present to the agent = Count as failed requirement
            
            Remember: Most real-world executions should score 4-6. Scores of 8+ should be EXCEPTIONAL.
            
            FINAL REMINDER BEFORE SCORING:
            - Default to 4-5 unless you have strong evidence for higher
            - Count ONLY truly perfect executions toward the percentage
            - Be your most critical self - find flaws first, then acknowledge successes
            - If you're considering a score above 7, re-examine for ANY imperfection
            - Server count is IRRELEVANT - using more servers is NOT better
            
            Please score based on COMPLETION PERCENTAGES and PROPORTIONAL SUCCESS, not absolute numbers.
            Return your evaluation scoring and reasoning in this exact JSON format:
            {{

            "task_fulfillment_reasoning": "Explain how well the agent fulfilled the detailed task objectives, referencing specific content from the CONCRETE TASK DESCRIPTION and what percentage was completed.",
            "grounding_reasoning": "Explain how well the agent's outputs were grounded in actual tool results versus unsupported claims.",
            "tool_appropriateness_reasoning": "Explain whether the tools selected were appropriate for each subtask requirement.",
            "parameter_accuracy_reasoning": "Explain the accuracy and completeness of parameters used in tool calls, noting any missing required parameters or incorrect values.",
            "dependency_awareness_reasoning": "Explain how well the agent understood and respected task dependencies (what percentage of dependencies were handled correctly), refer to the provided dependency analysis section.",
            "parallelism_efficiency_reasoning": "Explain the efficiency of execution, including use of parallelism and avoiding redundancy, refer to the provided dependency analysis section." 

            "task_fulfillment": X,
            "grounding": X,
            
            "tool_appropriateness": X,
            "parameter_accuracy": X,
            
            "dependency_awareness": X,
            "parallelism_and_efficiency": X,
            
            }}
            
            Return **only** the JSON object.
            """
        
        try:
            single_eval_start_time = time.time()
            logger.debug(f"Starting single LLM judge evaluation for task: {task[:100]}...")
            
            llm_start_time = time.time()
            response = await self.llm.get_completion(
                "You are an expert AI task execution evaluator. Score each dimension objectively based on evidence.", 
                prompt, 
                15000
            )
            llm_end_time = time.time()
            
            logger.debug(f"LLM response received: {response[:200]}...")
            
            parse_start_time = time.time()
            result = self.llm.clean_and_parse_json(response)
            parse_end_time = time.time()
            
            single_eval_total_time = time.time() - single_eval_start_time
            llm_time = llm_end_time - llm_start_time
            parse_time = parse_end_time - parse_start_time
            
            logger.info(f"LLM Judge Standard Timing:")
            logger.info(f"   Total evaluation time: {single_eval_total_time:.2f}s")
            logger.info(f"   LLM call time: {llm_time:.2f}s")
            logger.info(f"   Parsing time: {parse_time:.3f}s")
            logger.debug(f"Parsed result: {result}")
            
            # Extract 6 subdimension scores
            task_fulfillment = result.get('task_fulfillment')
            grounding = result.get('grounding')
            
            tool_appropriateness = result.get('tool_appropriateness')
            parameter_accuracy = result.get('parameter_accuracy')
            
            dependency_awareness = result.get('dependency_awareness')
            parallelism_and_efficiency = result.get('parallelism_and_efficiency')
            
            # Calculate aggregate scores (2 scores per category)
            task_completion_scores = [task_fulfillment, grounding]
            tool_selection_scores = [tool_appropriateness, parameter_accuracy]
            planning_scores = [dependency_awareness, parallelism_and_efficiency]
            
            task_completion_score = sum(task_completion_scores) / len(task_completion_scores) if task_completion_scores else 0
            tool_selection_score = sum(tool_selection_scores) / len(tool_selection_scores) if tool_selection_scores else 0
            planning_effectiveness_and_efficiency_score = sum(planning_scores) / len(planning_scores) if planning_scores else 0
            
            # Note: Removed flat_average_score calculation as it's no longer needed
            
            return {
                # 6 subdimension scores
                'task_fulfillment': task_fulfillment,
                'grounding': grounding,
                'tool_appropriateness': tool_appropriateness,
                'parameter_accuracy': parameter_accuracy,
                'dependency_awareness': dependency_awareness,
                'parallelism_and_efficiency': parallelism_and_efficiency,
                
                # 3 calculated aggregate scores
                'task_completion_score': task_completion_score,
                'tool_selection_score': tool_selection_score,
                'planning_effectiveness_and_efficiency_score': planning_effectiveness_and_efficiency_score,
                
                # Analysis text fields
                'task_completion_analysis': result.get('task_completion_analysis', ''),
                'tool_selection_analysis': result.get('tool_selection_analysis', ''),
                'planning_effectiveness_and_efficiency_analysis': result.get('planning_effectiveness_and_efficiency_analysis', '')
            }
            
        except Exception as e:
            logger.error(f"LLM judge evaluation failed: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise RuntimeError(f"LLM judge evaluation failed: {e}") from e
    
    def _create_execution_summary(self, execution_results: List[Dict[str, Any]], total_rounds: int, 
                                   accumulated_information: str = None) -> str:
        """Create a comprehensive summary of task execution including accumulated information"""
        summary_parts = []
        
        # Add tool execution statistics
        if not execution_results:
            summary_parts.append("No tools were executed.")
        else:
            successful_tools = [r for r in execution_results if safe_get(r, 'success')]
            failed_tools = [r for r in execution_results if not safe_get(r, 'success')]
            
            summary_parts.extend([
                f"Total rounds: {total_rounds}",
                f"Tools executed: {len(execution_results)}",
                f"Successful: {len(successful_tools)}",
                f"Failed: {len(failed_tools)}"
            ])
            
            if successful_tools:
                successful_tool_names = [safe_get(r, 'tool', 'unknown') for r in successful_tools]
                summary_parts.append(f"Successful tools: {', '.join(successful_tool_names)}")
            
            if failed_tools:
                failed_tool_names = [safe_get(r, 'tool', 'unknown') for r in failed_tools]
                summary_parts.append(f"Failed tools: {', '.join(failed_tool_names)}")
        
        execution_stats = "; ".join(summary_parts)
        
        # Add accumulated information if available
        if accumulated_information:            
            return f"{execution_stats}\n\n--- ACCUMULATED INFORMATION FROM EXECUTION ---\n{accumulated_information}"
        else:
            return execution_stats


class TaskEvaluator(BaseEvaluator):
    """
    Comprehensive task evaluator that combines execution analysis, LLM judgment, 
    and tool accuracy assessment.
    """
    
    def __init__(self, llm_provider: LLMProvider, enable_judge_stability: bool = False):
        super().__init__(llm_provider)
        self.llm_judge = LLMJudge(llm_provider, enable_judge_stability)
    
    async def evaluate(self, task: str, execution_results: List[Dict[str, Any]], 
                      final_solution: str, total_rounds: int, available_tools: Dict[str, Any],
                      planning_json_compliance: float = None,
                      accumulated_information: str = None,
                      concrete_task_description: str = None,
                      dependency_analysis: str = None) -> Optional[Dict[str, Any]]:
        """
        Comprehensive evaluation of task execution quality.
        
        Args:
            task: The task description presented to the agent (may be fuzzy)
            execution_results: List of tool execution results
            final_solution: The final solution provided
            total_rounds: Number of execution rounds
            available_tools: Dictionary of available tools
            planning_json_compliance: Pre-calculated planning JSON compliance from executor (optional)
            accumulated_information: Additional context from task execution (optional)
            concrete_task_description: Original concrete task description for evaluation reference (optional)
            
        Returns:
            Dictionary containing all evaluation metrics
        """
        logger.info("Starting comprehensive task evaluation...")
        
        try:
            # LLM judge evaluation  
            llm_scores = await self.llm_judge.evaluate_task_performance(
                task, final_solution, execution_results, total_rounds, available_tools, accumulated_information,
                concrete_task_description, dependency_analysis
            )
            
            # Use provided planning JSON compliance or default to 1.0
            if planning_json_compliance is None:
                planning_json_compliance = 1.0
                logger.debug("No planning JSON compliance provided, defaulting to 1.0")
            
            # Tool accuracy metrics
            tool_metrics = self._calculate_tool_accuracy_metrics(
                execution_results, available_tools, planning_json_compliance
            )
            
            # Server utilization metrics
            server_metrics = self._calculate_server_utilization_metrics(execution_results)
            
            evaluation = {
                **llm_scores,
                **tool_metrics,
                "server_utilization_metrics": server_metrics,
                "evaluation_timestamp": asyncio.get_event_loop().time()
            }
            
            logger.info("Task evaluation completed successfully")
            return evaluation
            
        except Exception as e:
            logger.error(f"Task evaluation failed: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return None
    
    def _calculate_tool_accuracy_metrics(self, execution_results: List[Dict[str, Any]], 
                                       available_tools: Dict[str, Any],
                                       planning_json_compliance: float = None) -> Dict[str, Any]:
        """Calculate tool selection and execution accuracy metrics"""
        if not execution_results:
            # planning_json_compliance should always be provided
            if planning_json_compliance is None:
                raise ValueError("planning_json_compliance parameter is required")
            
            # Return None for metrics that cannot be calculated without execution results
            # These should be excluded from averaging
            return {
                'input_schema_compliance': None,  # N/A - no tool calls to evaluate
                'valid_tool_name_rate': None,  # N/A - no tool calls to evaluate
                'execution_success_rate': None,  # N/A - no executions
                'valid_call_failure_rate': None,  # N/A - no valid calls
                'planning_json_compliance': planning_json_compliance  # This can still be evaluated
            }
        
        valid_tool_calls = 0
        schema_compliant_calls = 0
        successful_executions = 0
        valid_call_failures = 0
        
        for result in execution_results:
            tool_name = safe_get(result, 'tool', '')
            success = safe_get(result, 'success', False)
            parameters = safe_get(result, 'parameters', {})
            
            # Check if tool name is valid
            is_valid_tool = tool_name in available_tools
            if is_valid_tool:
                valid_tool_calls += 1
                
                # Check schema compliance for valid tools
                if self._check_schema_compliance(tool_name, parameters, available_tools):
                    schema_compliant_calls += 1
                
                # Track failures of valid tool calls (infrastructure issues)
                if not success:
                    valid_call_failures += 1
            
            # Track successful executions
            if success:
                successful_executions += 1
        
        total_calls = len(execution_results)
        
        # planning_json_compliance should always be provided
        if planning_json_compliance is None:
            raise ValueError("planning_json_compliance parameter is required")
        
        return {
            'input_schema_compliance': schema_compliant_calls / valid_tool_calls if valid_tool_calls > 0 else 0.0,
            'valid_tool_name_rate': valid_tool_calls / total_calls,
            'execution_success_rate': successful_executions / total_calls,
            'valid_call_failure_rate': valid_call_failures / valid_tool_calls if valid_tool_calls > 0 else 0.0,
            'planning_json_compliance': planning_json_compliance
        }
    
    def _check_schema_compliance(self, tool_name: str, parameters: Dict[str, Any], 
                               available_tools: Dict[str, Any]) -> bool:
        """Check if parameters comply with tool schema"""
        try:
            tool_info = available_tools.get(tool_name, {})
            input_schema = tool_info.get('input_schema', {})
            
            if not input_schema:
                return True  # No schema to validate against
            
            jsonschema.validate(parameters, input_schema)
            return True
            
        except (ValidationError, Exception):
            return False
    
    def _calculate_server_utilization_metrics(self, execution_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate metrics about server utilization and coordination"""
        if not execution_results:
            return {
                'server_count': 0,
                'cross_server_coordination': False,
                'server_distribution': {}
            }
        
        servers_used = set()
        server_counts = Counter()
        
        for result in execution_results:
            server = safe_get(result, 'server', '')
            if server:
                servers_used.add(server)
                server_counts[server] += 1
        
        return {
            'server_count': len(servers_used),
            'cross_server_coordination': len(servers_used) > 1,
            'server_distribution': dict(server_counts)
        }
