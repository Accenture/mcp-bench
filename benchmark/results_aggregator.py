#!/usr/bin/env python3
"""
Results Aggregator for MCP-Bench

This module handles the aggregation and statistical calculation of benchmark results.
It provides functionality to aggregate results at different levels:
- Model-level summary statistics
- Current metrics from ongoing tasks  
- Multi-file average metrics
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class ResultsAggregator:
    """Handles aggregation and statistical calculation of benchmark results"""
    
    def __init__(self):
        pass
    
    @staticmethod
    def safe_avg(values: List[Any]) -> float:
        """Calculate average of values, filtering out None values"""
        if not values:
            return 0.0
        filtered_values = [v for v in values if v is not None]
        return sum(filtered_values) / len(filtered_values) if filtered_values else 0.0

    def aggregate_model_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive summary statistics for a model's results"""
        # Results should never contain None - if they do, it's a bug
        if any(r is None for r in results):
            raise RuntimeError("Results list contains None values - this indicates a bug in task execution")
        
        completed_results = [r for r in results if r.get('status') == 'completed']
        total_results = len(results)
        
        if not completed_results:
            return self._get_empty_model_summary(total_results)
        
        # Initialize metric collectors for new 6-dimension LLM judge scores
        task_fulfillment_scores = []
        grounding_scores = []
        tool_appropriateness_scores = []
        parameter_accuracy_scores = []
        dependency_awareness_scores = []
        parallelism_efficiency_scores = []
        
        input_schema_compliance_scores = []
        valid_tool_name_rate_scores = []
        execution_success_rates = []
        valid_call_failure_rates = []
        
        
        execution_times = []
        agent_execution_times = []
        evaluation_times = []
        total_rounds = []
        tool_calls_counts = []
        
        servers_used_counts = []
        cross_server_tasks = 0
        
        # Extract all metrics from completed results
        for idx, result in enumerate(completed_results):
            evaluation = result.get('evaluation')
            if evaluation is None:
                logger.error(f"No evaluation found in result {idx}, task may have failed evaluation")
                raise ValueError(f"Missing evaluation in result {idx}")
            
            # LLM Judge metrics (new 6-dimension scoring)
            self._validate_llm_judge_fields(evaluation, idx)
                
            task_fulfillment_scores.append(evaluation['task_fulfillment'])
            grounding_scores.append(evaluation['grounding'])
            tool_appropriateness_scores.append(evaluation.get('tool_appropriateness', 0))
            parameter_accuracy_scores.append(evaluation.get('parameter_accuracy', 0))
            dependency_awareness_scores.append(evaluation.get('dependency_awareness', 0))
            parallelism_efficiency_scores.append(evaluation.get('parallelism_and_efficiency', 0))
            
            
            # Accuracy metrics - these fields must exist but can be None
            self._validate_accuracy_fields(evaluation, idx)
                
            # Only append non-None values for proper averaging
            if evaluation['input_schema_compliance'] is not None:
                input_schema_compliance_scores.append(evaluation['input_schema_compliance'])
            if evaluation['valid_tool_name_rate'] is not None:
                valid_tool_name_rate_scores.append(evaluation['valid_tool_name_rate'])
            if evaluation['execution_success_rate'] is not None:
                execution_success_rates.append(evaluation['execution_success_rate'])
            if evaluation['valid_call_failure_rate'] is not None:
                valid_call_failure_rates.append(evaluation['valid_call_failure_rate'])
            
            # Performance metrics
            self._validate_performance_fields(result, idx)
                
            execution_times.append(result['execution_time'])
            
            # Agent execution time (may not exist in older results)
            if 'agent_execution_time' in result:
                agent_execution_times.append(result['agent_execution_time'])
            
            # Evaluation time (may not exist in older results)
            if 'evaluation_time' in result:
                evaluation_times.append(result['evaluation_time'])
                
            total_rounds.append(result['total_rounds'])
            
            # Tool calls count
            self._validate_execution_results(result, idx)
            execution_results = result['execution_results']
            tool_calls_counts.append(len(execution_results))
            
            # Server utilization
            server_metrics = evaluation.get('server_utilization_metrics', {})
            if not isinstance(server_metrics, dict):
                logger.error(f"server_utilization_metrics is not a dict in result {idx}: {type(server_metrics)}")
                raise TypeError(f"server_utilization_metrics must be dict in result {idx}")
            
            if 'server_count' not in server_metrics:
                logger.error(f"Missing server_count in server_utilization_metrics for result {idx}")
                raise KeyError(f"server_count missing in server_metrics for result {idx}")
                
            server_count = server_metrics['server_count']
            servers_used_counts.append(server_count)
            
            if server_metrics.get('cross_server_coordination', False):
                cross_server_tasks += 1
        
        # LLM Judge combined score (average of 6 dimensions)
        llm_combined_scores = []
        for i in range(len(task_fulfillment_scores)):
            combined = (task_fulfillment_scores[i] + grounding_scores[i] + 
                       tool_appropriateness_scores[i] + parameter_accuracy_scores[i] +
                       dependency_awareness_scores[i] + parallelism_efficiency_scores[i]) / 6
            llm_combined_scores.append(combined)
        
        return {
            'task_statistics': {
                'total_tasks': total_results,
                'completed_tasks': len(completed_results),
                'failed_tasks': total_results - len(completed_results),
                'completion_rate': len(completed_results) / total_results if total_results > 0 else 0.0
            },
            'llm_judge_metrics': {
                'avg_task_fulfillment_score': self.safe_avg(task_fulfillment_scores),
                'avg_grounding_score': self.safe_avg(grounding_scores),
                'avg_tool_appropriateness_score': self.safe_avg(tool_appropriateness_scores),
                'avg_parameter_accuracy_score': self.safe_avg(parameter_accuracy_scores),
                'avg_dependency_awareness_score': self.safe_avg(dependency_awareness_scores),
                'avg_parallelism_efficiency_score': self.safe_avg(parallelism_efficiency_scores),
                'avg_llm_judge_combined': self.safe_avg(llm_combined_scores)
            },
            'accuracy_metrics': {
                'avg_input_schema_compliance': self.safe_avg(input_schema_compliance_scores),
                'avg_valid_tool_name_rate': self.safe_avg(valid_tool_name_rate_scores),
                'avg_execution_success_rate': self.safe_avg(execution_success_rates),
                'avg_valid_call_failure_rate': self.safe_avg(valid_call_failure_rates)
            },
            'performance_metrics': {
                'avg_execution_time': self.safe_avg(execution_times),
                'avg_agent_execution_time': self.safe_avg(agent_execution_times),
                'avg_evaluation_time': self.safe_avg(evaluation_times),
                'avg_total_rounds': self.safe_avg(total_rounds),
                'avg_tool_calls_per_task': self.safe_avg(tool_calls_counts)
            },
            'server_utilization_metrics': {
                'avg_servers_used': self.safe_avg(servers_used_counts),
                'cross_server_coordination_rate': cross_server_tasks / len(completed_results) if completed_results else 0.0
            }
        }

    def aggregate_current_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate current average metrics from completed tasks"""
        if any(r is None for r in results):
            raise RuntimeError("Results list contains None values - this indicates a bug in task execution")
        
        completed_results = [r for r in results if r.get('status') == 'completed']
        
        if not completed_results:
            logger.warning("No completed results to analyze")
            return self._get_empty_current_metrics()
        
        # Initialize collectors for core metrics only (6 dimensions)
        task_fulfillment_scores = []
        grounding_scores = []
        tool_appropriateness_scores = []
        parameter_accuracy_scores = []
        dependency_awareness_scores = []
        parallelism_and_efficiency_scores = []
        
        # Aggregate scores
        task_completion_scores = []
        tool_selection_scores = []
        planning_effectiveness_scores = []
        
        # Tool accuracy metrics
        input_schema_compliance_scores = []
        valid_tool_name_rate_scores = []
        execution_success_rates = []
        
        
        execution_times = []
        agent_execution_times = []
        evaluation_times = []
        total_rounds = []
        tool_calls_counts = []
        
        # Token usage tracking
        total_output_tokens_list = []
        total_prompt_tokens_list = []
        total_tokens_list = []
        
        # Collect metrics
        for result in completed_results:
            evaluation = result.get('evaluation')
            if evaluation is None:
                logger.warning(f"Skipping result without evaluation for task {result.get('task_id', 'unknown')}")
                continue  # Skip results with failed evaluation
            
            # Validate required fields
            self._validate_current_metrics_fields(evaluation)
            
            # LLM Judge metrics - 6 subdimensions (no defaults)
            task_fulfillment_scores.append(evaluation['task_fulfillment'])
            grounding_scores.append(evaluation['grounding'])
            tool_appropriateness_scores.append(evaluation['tool_appropriateness'])
            parameter_accuracy_scores.append(evaluation.get('parameter_accuracy', 0))
            dependency_awareness_scores.append(evaluation['dependency_awareness'])
            parallelism_and_efficiency_scores.append(evaluation['parallelism_and_efficiency'])
            
            # LLM Judge metrics - 3 aggregate scores (no defaults)
            task_completion_scores.append(evaluation['task_completion_score'])
            tool_selection_scores.append(evaluation['tool_selection_score'])
            planning_effectiveness_scores.append(evaluation['planning_effectiveness_and_efficiency_score'])
            
            # Tool accuracy metrics (no defaults)
            input_schema_compliance_scores.append(evaluation['input_schema_compliance'])
            valid_tool_name_rate_scores.append(evaluation['valid_tool_name_rate'])
            execution_success_rates.append(evaluation['execution_success_rate'])
            
            
            # Performance
            execution_times.append(result['execution_time'])
            
            # Agent execution time (may not exist in older results)
            if 'agent_execution_time' in result:
                agent_execution_times.append(result['agent_execution_time'])
            
            # Evaluation time (may not exist in older results)
            if 'evaluation_time' in result:
                evaluation_times.append(result['evaluation_time'])
            
            # Collect total rounds and tool calls count
            if 'total_rounds' in result:
                total_rounds.append(result['total_rounds'])
            
            if 'execution_results' in result:
                execution_results = result['execution_results']
                if isinstance(execution_results, list):
                    tool_calls_counts.append(len(execution_results))
            
            # Collect token usage
            if 'total_output_tokens' in result:
                total_output_tokens_list.append(result['total_output_tokens'])
            if 'total_prompt_tokens' in result:
                total_prompt_tokens_list.append(result['total_prompt_tokens'])
            if 'total_tokens' in result:
                total_tokens_list.append(result['total_tokens'])
        
        return {
            # 4 aggregate scores
            'task_completion_score': self.safe_avg(task_completion_scores),
            'tool_selection_score': self.safe_avg(tool_selection_scores),
            'planning_effectiveness_and_efficiency_score': self.safe_avg(planning_effectiveness_scores),
            
            # 6 subdimension scores
            'task_fulfillment': self.safe_avg(task_fulfillment_scores),
            'grounding': self.safe_avg(grounding_scores),
            'tool_appropriateness': self.safe_avg(tool_appropriateness_scores),
            'parameter_accuracy': self.safe_avg(parameter_accuracy_scores),
            'dependency_awareness': self.safe_avg(dependency_awareness_scores),
            'parallelism_and_efficiency': self.safe_avg(parallelism_and_efficiency_scores),
            
            # Tool accuracy metrics
            'input_schema_compliance': self.safe_avg(input_schema_compliance_scores),
            'valid_tool_name_rate': self.safe_avg(valid_tool_name_rate_scores),
            'tool_call_success_rate': self.safe_avg(execution_success_rates),
            
            # Performance and success rate
            'avg_execution_time': self.safe_avg(execution_times),
            'avg_agent_execution_time': self.safe_avg(agent_execution_times),
            'avg_evaluation_time': self.safe_avg(evaluation_times),
            'task_success_rate': len(completed_results) / len(results) if results else 0,
            
            # Execution statistics
            'avg_total_rounds': self.safe_avg(total_rounds),
            'avg_tool_calls_per_task': self.safe_avg(tool_calls_counts),
            
            # Token usage statistics
            'avg_output_tokens': self.safe_avg(total_output_tokens_list),
            'avg_prompt_tokens': self.safe_avg(total_prompt_tokens_list),
            'avg_total_tokens': self.safe_avg(total_tokens_list),
        }

    def aggregate_multi_file_metrics(self, all_files_metrics: Dict[str, Dict]) -> Dict[str, Dict]:
        """Calculate average metrics across all task files"""
        model_averages = {}
        
        # Get all models
        all_models = set()
        for file_data in all_files_metrics.values():
            if 'final_metrics' in file_data:
                all_models.update(file_data['final_metrics'].keys())
        
        for model_name in all_models:
            model_metrics = []
            for file_data in all_files_metrics.values():
                if 'final_metrics' in file_data and model_name in file_data['final_metrics']:
                    model_metrics.append(file_data['final_metrics'][model_name])
            
            if model_metrics:
                # Calculate average for each metric, handling nested dictionaries
                avg_metrics = self._aggregate_nested_metrics(model_metrics)
                model_averages[model_name] = avg_metrics
        
        return model_averages
    
    def _aggregate_nested_metrics(self, model_metrics: List[Dict]) -> Dict:
        """Recursively aggregate nested metrics"""
        avg_metrics = {}
        
        # Get all keys from all metrics
        all_keys = set()
        for metrics in model_metrics:
            if isinstance(metrics, dict):
                all_keys.update(metrics.keys())
        
        for key in all_keys:
            values = []
            nested_dicts = []
            
            for metrics in model_metrics:
                if isinstance(metrics, dict) and key in metrics:
                    value = metrics[key]
                    
                    # Handle nested dictionaries
                    if isinstance(value, dict):
                        nested_dicts.append(value)
                    # Handle numeric values (but not booleans)
                    elif isinstance(value, (int, float)) and not isinstance(value, bool):
                        values.append(value)
            
            # If we have nested dictionaries, recursively aggregate them
            if nested_dicts:
                avg_metrics[key] = self._aggregate_nested_metrics(nested_dicts)
            # If we have numeric values, calculate the average
            elif values:
                avg_metrics[key] = sum(values) / len(values)
            else:
                avg_metrics[key] = 0
        
        return avg_metrics

    def _get_empty_model_summary(self, total_results: int) -> Dict[str, Any]:
        """Get empty model summary for when no tasks completed"""
        return {
            'task_statistics': {
                'total_tasks': total_results,
                'completed_tasks': 0,
                'failed_tasks': total_results,
                'completion_rate': 0.0
            },
            'llm_judge_metrics': {
                'avg_task_fulfillment_score': 0.0,
                'avg_grounding_score': 0.0,
                'avg_tool_appropriateness_score': 0.0,
                'avg_parameter_accuracy_score': 0.0,
                'avg_dependency_awareness_score': 0.0,
                'avg_parallelism_efficiency_score': 0.0,
                'avg_llm_judge_combined': 0.0
            },
            'accuracy_metrics': {
                'avg_input_schema_compliance': 0.0,
                'avg_valid_tool_name_rate': 0.0,
                'avg_execution_success_rate': 0.0,
                'avg_valid_call_failure_rate': 0.0,
                'avg_dependency_chain_compliance': 0.0
            },
            'performance_metrics': {
                'avg_execution_time': 0.0,
                'avg_total_rounds': 0.0,
                'avg_tool_calls_per_task': 0.0
            },
            'server_utilization_metrics': {
                'avg_servers_used': 0.0,
                'cross_server_coordination_rate': 0.0
            }
        }

    def _get_empty_current_metrics(self) -> Dict[str, Any]:
        """Get empty current metrics for when no tasks completed"""
        return {
            'task_completion_score': 0.0,
            'tool_selection_score': 0.0,
            'planning_effectiveness_and_efficiency_score': 0.0,
            'task_fulfillment': 0.0,
            'completeness': 0.0,
            'grounding': 0.0,
            'relevance': 0.0,
            'tool_appropriateness': 0.0,
            'intent_alignment': 0.0,
            'output_integration': 0.0,
            'structural_coherence': 0.0,
            'dependency_awareness': 0.0,
            'parallelism_and_efficiency': 0.0,
            'input_schema_compliance': 0.0,
            'valid_tool_name_rate': 0.0,
            'execution_success_rate': 0.0,
            'execution_dependency_chain_compliance': 0.0,
            'avg_execution_time': 0.0
        }

    def _validate_llm_judge_fields(self, evaluation: Dict[str, Any], idx: int):
        """Validate LLM judge fields are present"""
        required_fields = ['task_fulfillment', 'grounding']
        for field in required_fields:
            if field not in evaluation:
                logger.error(f"Missing {field} in evaluation for result {idx}")
                raise KeyError(f"{field} missing in result {idx}")

    def _validate_accuracy_fields(self, evaluation: Dict[str, Any], idx: int):
        """Validate accuracy fields are present"""
        required_fields = ['input_schema_compliance', 'valid_tool_name_rate', 
                          'execution_success_rate', 'valid_call_failure_rate']
        for field in required_fields:
            if field not in evaluation:
                logger.error(f"Missing {field} in evaluation for result {idx}")
                raise KeyError(f"{field} missing in result {idx}")

    def _validate_performance_fields(self, result: Dict[str, Any], idx: int):
        """Validate performance fields are present"""
        required_fields = ['execution_time', 'total_rounds']
        for field in required_fields:
            if field not in result:
                logger.error(f"Missing {field} in result {idx}")
                raise KeyError(f"{field} missing in result {idx}")

    def _validate_execution_results(self, result: Dict[str, Any], idx: int):
        """Validate execution results field"""
        if 'execution_results' not in result:
            logger.error(f"Missing execution_results in result {idx}")
            raise KeyError(f"execution_results missing in result {idx}")
        execution_results = result['execution_results']
        if not isinstance(execution_results, list):
            logger.error(f"execution_results is not a list in result {idx}: {type(execution_results)}")
            raise TypeError(f"execution_results must be list in result {idx}")

    def _validate_current_metrics_fields(self, evaluation: Dict[str, Any]):
        """Validate all required fields for current metrics calculation"""
        # Check for all required fields and raise error if missing
        required_llm_fields = ['task_fulfillment', 'grounding', 
                               'tool_appropriateness', 'dependency_awareness', 'parallelism_and_efficiency']
        required_aggregate_fields = ['task_completion_score', 'tool_selection_score', 
                                    'planning_effectiveness_and_efficiency_score']
        required_accuracy_fields = ['input_schema_compliance', 'valid_tool_name_rate', 
                                   'execution_success_rate']
        
        # Check LLM Judge subdimensions
        missing_llm = [f for f in required_llm_fields if f not in evaluation]
        if missing_llm:
            logger.error(f"Missing LLM Judge subdimensions: {missing_llm}")
            raise KeyError(f"Missing LLM Judge fields: {missing_llm}")
        
        # Check aggregate scores
        missing_aggregate = [f for f in required_aggregate_fields if f not in evaluation]
        if missing_aggregate:
            logger.error(f"Missing aggregate scores: {missing_aggregate}")
            raise KeyError(f"Missing aggregate score fields: {missing_aggregate}")
        
        # Check accuracy metrics
        missing_accuracy = [f for f in required_accuracy_fields if f not in evaluation]
        if missing_accuracy:
            logger.error(f"Missing accuracy metrics: {missing_accuracy}")
            raise KeyError(f"Missing accuracy fields: {missing_accuracy}")
        
