#!/usr/bin/env python3
"""
Results Formatter for MCP-Bench

This module handles the formatting and display of benchmark results.
It provides functionality to format results for different display contexts:
- Current metrics during task execution
- Single task detailed metrics
- Multi-file results summary
- Average metrics across files
"""

import os
import json
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


def execution_results_to_text(execution_results: List[Dict[str, Any]]) -> str:
    """Convert execution results to text representation with layer organization"""
    if not execution_results:
        return "Execution Sequence: Empty"
    
    lines = []
    lines.append(f"Execution Sequence ({len(execution_results)} tools):")
    
    # Try to organize by layers
    layers_dict = {}
    no_layer_tools = []
    
    # Validate no None results first
    for i, result in enumerate(execution_results):
        if result is None:
            raise RuntimeError(f"execution_results[{i}] is None - this indicates a bug in task execution")
    
    # Check if we have planned_layer information (single-round execution)
    has_planned_layers = any(result.get('planned_layer') is not None for result in execution_results)
    
    for i, result in enumerate(execution_results):
            
        tool = result.get('tool', '')
        success = "SUCCESS" if result.get('success') else "FAILED"
        round_num = result.get('round_num', '')
        planned_layer = result.get('planned_layer')
        parameters = result.get('parameters', {})
        
        # Create tool representation with parameters
        # Tool already contains full name (e.g., "@smithery-ai/google-maps:maps_geocode")
        # Format parameters - truncate if too long
        if parameters:
            params_str = json.dumps(parameters, ensure_ascii=False)
            # Truncate long parameters
            if len(params_str) > 100:
                params_str = params_str[:97] + "..."
            tool_repr = f"{success} {tool} {params_str}"
        else:
            tool_repr = f"{success} {tool}"
        
        if has_planned_layers and planned_layer is not None:
            # Use planned_layer for single-round execution
            if planned_layer not in layers_dict:
                layers_dict[planned_layer] = []
            layers_dict[planned_layer].append((tool_repr, round_num))
        elif round_num:
            # For multi-round execution, group by round number
            # Each round is essentially a layer
            round_layer = round_num - 1  # Convert 1-based round to 0-based layer for consistency
            if round_layer not in layers_dict:
                layers_dict[round_layer] = []
            layers_dict[round_layer].append((tool_repr, round_num))
        else:
            no_layer_tools.append((i, tool_repr))
    
    # Display by layers
    if layers_dict:
        lines.append("\nExecution Layers:")
        for layer in sorted(layers_dict.keys()):
            tools_in_layer = layers_dict[layer]
            # For single-round execution with planned layers, show step number
            # For multi-round execution, show round number
            if has_planned_layers:
                # In single-round, layer corresponds to execution step
                lines.append(f"  Layer {layer} (Step {layer + 1}):")
            else:
                # In multi-round, show the actual round number
                round_nums = set(r for _, r in tools_in_layer if r)
                if round_nums:
                    round_info = f" (Round {', '.join(str(r) for r in sorted(round_nums))})"
                else:
                    round_info = ""
                lines.append(f"  Layer {layer}{round_info}:")
            
            for tool_repr, _ in tools_in_layer:
                lines.append(f"    {tool_repr}")
    
    # Display tools without layer info
    if no_layer_tools:
        lines.append("\n  No layer info:")
        for idx, tool_repr in no_layer_tools:
            lines.append(f"    [{idx}] {tool_repr}")
    
    return "\n".join(lines)


class ResultsFormatter:
    """Handles formatting and display of benchmark results"""
    
    def __init__(self):
        self.last_cumulative_metrics = {}
    
    def format_current_metrics(self, model_name: str, completed: int, total: int, 
                               metrics: Dict[str, Any], task_file: str = None):
        """Display current metrics in a formatted way"""
        if not metrics:
            return
        
        # Update tracked cumulative metrics
        self.last_cumulative_metrics = metrics.copy()
        
        logger.info(f"\n{'='*80}")
        file_info = f" ({os.path.basename(task_file)})" if task_file else ""
        logger.info(f"Cumulative Metrics for {model_name}{file_info} ({completed}/{total} tasks completed):")
        logger.info(f"{'='*80}")
        
        logger.info(f"  LLM Judge Scores:")
        logger.info(f"    • Task Completion Score: {metrics.get('task_completion_score', 0):.3f}")
        logger.info(f"    • Tool Selection Score: {metrics.get('tool_selection_score', 0):.3f}")
        logger.info(f"    • Planning Effectiveness Score: {metrics.get('planning_effectiveness_and_efficiency_score', 0):.3f}")
        logger.info(f"  Subdimension Scores:")
        logger.info(f"    Task: Fulfillment {metrics.get('task_fulfillment', 0):.3f}, Grounding {metrics.get('grounding', 0):.3f}")
        logger.info(f"    Tool: Appropriateness {metrics.get('tool_appropriateness', 0):.3f}, Parameter Accuracy {metrics.get('parameter_accuracy', 0):.3f}")
        logger.info(f"    Plan: Dependency {metrics.get('dependency_awareness', 0):.3f}, Efficiency {metrics.get('parallelism_and_efficiency', 0):.3f}")
        
        logger.info(f"  Tool Accuracy Metrics:")
        # Handle None values for percentage metrics
        schema_comp = metrics.get('input_schema_compliance')
        valid_name = metrics.get('valid_tool_name_rate')
        success_rate = metrics.get('tool_call_success_rate')
        
        logger.info(f"    • Input Schema Compliance: {'N/A' if schema_comp is None else f'{schema_comp:.2%}'} (among valid tool names)")
        logger.info(f"    • Valid Tool Name Rate: {'N/A' if valid_name is None else f'{valid_name:.2%}'}")
        logger.info(f"    • Tool Call Success Rate: {'N/A' if success_rate is None else f'{success_rate:.2%}'}")
        
        
        logger.info(f"  Execution Statistics:")
        logger.info(f"    • Avg Rounds per Task: {metrics.get('avg_total_rounds', 0):.2f}")
        logger.info(f"    • Avg Tool Calls per Task: {metrics.get('avg_tool_calls_per_task', 0):.2f}")
        
        logger.info(f"  Token Usage (OpenAI Tokenizer):")
        logger.info(f"    • Avg Output Tokens per Task: {metrics.get('avg_output_tokens', 0):.0f}")
        logger.info(f"    • Avg Prompt Tokens per Task: {metrics.get('avg_prompt_tokens', 0):.0f}")
        logger.info(f"    • Avg Total Tokens per Task: {metrics.get('avg_total_tokens', 0):.0f}")
        
        logger.info(f"  Runtime:")
        logger.info(f"    • Avg Agent Execution Time: {metrics.get('avg_agent_execution_time', 0):.1f}s")
        logger.info(f"    • Avg Judge Pipeline Time: {metrics.get('avg_evaluation_time', 0):.1f}s")
        logger.info(f"{'='*80}\n")
    
    def format_single_task_report(self, task_id: str, evaluation: Dict[str, Any], 
                                  dependency_structures: List[Dict[str, Any]] = None):
        """Display metrics for a single completed task"""
        logger.info(f"  Task {task_id} Individual Metrics:")
        logger.info(f"    LLM Judge Scores: "
                   f"Task={evaluation.get('task_completion_score', 0):.3f}, "
                   f"Tool={evaluation.get('tool_selection_score', 0):.3f}, "
                   f"Planning={evaluation.get('planning_effectiveness_and_efficiency_score', 0):.3f}")
        
        # Handle None values for tool accuracy metrics
        schema_compliance = evaluation.get('input_schema_compliance')
        valid_name_rate = evaluation.get('valid_tool_name_rate')
        success_rate = evaluation.get('execution_success_rate')
        json_compliance = evaluation.get('planning_json_compliance')
        
        logger.info(f"    Tool Accuracy: "
                   f"Schema={'N/A' if schema_compliance is None else f'{schema_compliance:.1%}'}, "
                   f"ValidName={'N/A' if valid_name_rate is None else f'{valid_name_rate:.1%}'}, "
                   f"Success={'N/A' if success_rate is None else f'{success_rate:.1%}'}, "
                   f"JSONCompliance={'N/A' if json_compliance is None else f'{json_compliance:.1%}'}")
        
        
        # Display dependency structures if available
        if dependency_structures:
            logger.info("    Dependency Structures:")
            for i, structure in enumerate(dependency_structures, 1):
                structure_id = structure.get('id', f'Structure {i}')
                structure_type = structure.get('type', 'unknown')
                description = structure.get('description', '')
                edges = structure.get('edges', [])
                nodes = structure.get('nodes', [])
                
                # Check if this structure has violations
                has_violations = structure_id in violations_by_structure
                violation_marker = " [VIOLATED]" if has_violations else ""
                
                # Display structure header
                logger.info(f"      [{structure_id}] ({structure_type}): {description}{violation_marker}")
                
                # Display dependencies based on edges
                if edges:
                    for edge in edges:
                        if isinstance(edge, list) and len(edge) >= 2:
                            prerequisite = edge[0].split(':')[-1] if ':' in edge[0] else edge[0]
                            dependent = edge[1].split(':')[-1] if ':' in edge[1] else edge[1]
                            
                            # Check if this specific edge was violated
                            edge_violated = False
                            violation_detail = ""
                            if has_violations:
                                for v in violations_by_structure[structure_id]:
                                    if v['prerequisite'] == prerequisite and v['dependent'] == dependent:
                                        edge_violated = True
                                        if v['violation_type'] == 'no_prior_prerequisite':
                                            violation_detail = f" [VIOLATED: {dependent} in round {v['dependent_round']}, {prerequisite} earliest in round {v['earliest_prereq_round']}]"
                                        elif v['violation_type'] == 'same_round':
                                            prereq_round = v.get('earliest_prereq_round', 'unknown')
                                            violation_detail = f" [VIOLATED: both in round {prereq_round}]"
                                        else:
                                            prereq_round = v.get('earliest_prereq_round', 'unknown')
                                            violation_detail = f" [VIOLATED: {dependent} in round {v['dependent_round']}, {prerequisite} in round {prereq_round}]"
                                        break
                            
                            logger.info(f"        → {prerequisite} must execute before {dependent}{violation_detail}")
                elif structure_type == "parallel_flat" or not edges:
                    # No dependencies - all tools can run in parallel
                    if nodes:
                        tool_names = [n.split(':')[-1] if ':' in n else n for n in nodes[:5]]
                        if len(nodes) > 5:
                            logger.info(f"        → All {len(nodes)} tools can execute in parallel ({', '.join(tool_names)}, ...)")
                        else:
                            logger.info(f"        → All tools can execute in parallel: {', '.join(tool_names)}")
                    else:
                        logger.info(f"        → No dependencies (free execution order)")
            
                        if violation['violation_type'] == 'no_prior_prerequisite':
                            logger.info(f"      [{violation['structure_id']}] {violation['dependent']} (round {violation['dependent_round']}) executed without prior {violation['prerequisite']} (earliest: round {violation['earliest_prereq_round']})")
                        elif violation['violation_type'] == 'same_round':
                            prereq_round = violation.get('earliest_prereq_round', 'unknown')
                            logger.info(f"      [{violation['structure_id']}] {violation['prerequisite']} and {violation['dependent']} executed in same round {prereq_round}")
                        else:
                            prereq_round = violation.get('earliest_prereq_round', 'unknown')
                            logger.info(f"      [{violation['structure_id']}] {violation['dependent']} (round {violation['dependent_round']}) executed before {violation['prerequisite']} (round {prereq_round})")
        
        # Display LLM Judge subdimension reasoning
        reasoning_fields = [
            ('task_fulfillment_reasoning', 'Task Fulfillment'),
            ('grounding_reasoning', 'Grounding'),
            ('tool_appropriateness_reasoning', 'Tool Appropriateness'),
            ('parameter_accuracy_reasoning', 'Parameter Accuracy'),
            ('dependency_awareness_reasoning', 'Dependency Awareness'),
            ('parallelism_efficiency_reasoning', 'Parallelism & Efficiency')
        ]
        
        # Check if any reasoning fields exist
        has_reasoning = any(evaluation.get(field_name) for field_name, _ in reasoning_fields)
        
        if has_reasoning:
            logger.info("    LLM Judge Subdimension Reasoning:")
            
            for field_name, display_name in reasoning_fields:
                reasoning = evaluation.get(field_name)
                if reasoning:
                    logger.info(f"      {display_name}:")
                    # Handle both string and dict/other formats
                    if isinstance(reasoning, str):
                        reasoning_text = reasoning
                    elif isinstance(reasoning, dict):
                        import json
                        reasoning_text = json.dumps(reasoning, indent=2)
                    else:
                        reasoning_text = str(reasoning)
                    
                    # Format the reasoning text with proper indentation
                    reasoning_lines = reasoning_text.strip().split('\n')
                    for line in reasoning_lines:
                        if line.strip():
                            logger.info(f"        {line.strip()}")
