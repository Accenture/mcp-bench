#!/usr/bin/env python3
"""
Task Synthesis for MCP-Benchmark
Generates tasks with fuzzy conversion as separate important stage
"""

import json
import logging
import random
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from llm.provider import LLMProvider

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskQualityEvaluator:
    """Evaluates task quality on solvability and utility dimensions"""
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider
        self.solvability_threshold = 9.0  # Strict threshold for solvability
        self.utility_threshold = 5.0  # Lower threshold for utility
        
    async def evaluate_task_quality(self, task: Dict[str, Any], tools: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate task quality on two dimensions:
        1. Solvability: Can the task be completed with the given tools? Task should be executable and solvable by using the provided tools. You need to pay attention to the function and the output of the provided tools.
        2. Utility: Does the task provide real business/research value?
        
        Returns:
            Dict with solvability_score, utility_score, and feedback
        """
        
        tool_descriptions = self._format_tools_for_eval(tools)
        
        prompt = f"""Evaluate this task's quality on two dimensions:

Task Description:
{task.get('task_description', '')}

Fuzzy Description (what the agent sees):
{task.get('fuzzy_description', '')}

Available Tools:
{tool_descriptions}

EVALUATION CRITERIA:

1. SOLVABILITY (1-10):
   - 10: All required data is provided, tools perfectly match needs, clear success criteria
   - 8-9: Task is clearly solvable with the given tools, minor ambiguities acceptable
   - 6-7: Mostly solvable but some steps may be challenging or unclear
   - 4-5: Significant gaps in tool coverage or data requirements
   - 1-3: Task cannot be meaningfully completed with available tools

   Consider:
   - Are all necessary tools available?
   - Is all required data provided (no external dependencies)?
   - Can the agent achieve the stated goal with these tools based on the function and output of the tools?
   - Are success criteria clear and measurable?

2. UTILITY (1-10):
   - 10: Critical business/research value, addresses real-world problem perfectly
   - 8-9: Strong practical value, useful for decision-making or operations
   - 6-7: Moderate value, interesting but not critical
   - 4-5: Limited practical value, mostly academic exercise
   - 1-3: Trivial or artificial task with no real-world application

   Consider:
   - Does this address a real business or research need?
   - Would the results be actionable and valuable?
   - Is the complexity justified by the outcome?
   - Does it test meaningful agent capabilities?

Provide scores and brief feedback in JSON format:
{{
  "solvability_score": <number 1-10>,
  "utility_score": <number 1-10>,
  "solvability_feedback": "Brief explanation of solvability assessment",
  "utility_feedback": "Brief explanation of utility assessment"
}}"""

        try:
            response = await self.llm.get_completion(
                system_prompt="You are an expert at evaluating AI benchmark task quality.",
                user_prompt=prompt,
                max_tokens=5000
            )
            
            # Parse evaluation response
            import json
            import re
            
            # Try direct JSON parsing
            try:
                evaluation = json.loads(response)
            except:
                # Try to extract JSON from response
                json_match = re.search(r'\{[^{}]*"solvability_score"[^{}]*\}', response, re.DOTALL)
                if json_match:
                    evaluation = json.loads(json_match.group())
                else:
                    # Default low scores if parsing fails
                    logger.error(f"Failed to parse quality evaluation: {response[:200]}")
                    return {
                        'solvability_score': 0.0,
                        'utility_score': 0.0,
                        'solvability_feedback': 'Failed to evaluate',
                        'utility_feedback': 'Failed to evaluate'
                    }
            
            # Ensure scores are floats
            evaluation['solvability_score'] = float(evaluation.get('solvability_score', 1))
            evaluation['utility_score'] = float(evaluation.get('utility_score', 1))
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating task quality: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                'solvability_score': 0.0,
                'utility_score': 0.0,
                'solvability_feedback': f'Evaluation error: {str(e)}',
                'utility_feedback': f'Evaluation error: {str(e)}'
            }
    
    def _format_tools_for_eval(self, tools: Dict[str, Any]) -> str:
        """Format tools for evaluation prompt"""
        formatted = ""
        for tool_name, tool_info in tools.items():
            if tool_info is None:
                logger.error(f"Tool {tool_name} has None info in eval! Tools dict keys: {list(tools.keys())[:10]}")
                continue
            
            formatted += f"\nTool: `{tool_name}` (Server: {tool_info.get('server', 'unknown')})\n"
            formatted += f"  Description: {tool_info.get('description', 'No description')}\n"
            
            input_schema = tool_info.get('input_schema')
            if input_schema:
                schema_str = json.dumps(input_schema, indent=2)
                formatted += f"  Input Schema:\n```json\n{schema_str}\n```\n"
        
        return formatted
    
    def meets_quality_threshold(self, evaluation: Dict[str, Any]) -> bool:
        """Check if task meets quality thresholds (solvability ≥ 9.0, utility ≥ 5.0)"""
        solvability = evaluation.get('solvability_score', 0)
        utility = evaluation.get('utility_score', 0)
        return solvability >= self.solvability_threshold and utility >= self.utility_threshold


class TaskSynthesizer:
    """Task synthesizer - two stages: task generation + fuzzy conversion"""
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider
        self.quality_evaluator = TaskQualityEvaluator(llm_provider)
        self.max_retries_per_task = 5
        # Common distraction servers pool
        self.distraction_server_pool = [
            "Bibliomantic", "Context7", "FruityVice", "Google Maps", 
            "Huge Icons", "Math MCP", "NASA Data", "National Parks",
            "Unit Converter", "Wikipedia", "Weather Data",
            "Paper Search", "Reddit", "OpenAPI Spec",
            "DEX Paprika", "Hugging Face", "OSINT Intelligence", "Game Search",
            "Call for Papers", "Met Museum", "Medical Calculator", "NixOS"
        ]
        
    async def generate_tasks(self, 
                           tools: Dict[str, Any], 
                           server_name: str,
                           num_tasks: int = 5) -> List[Dict[str, Any]]:
        """
        Generate tasks in two stages with quality evaluation:
        1. Generate detailed task descriptions
        2. Create fuzzy versions with evidence requirements
        3. Evaluate quality and retry if below threshold
        
        Args:
            tools: Available tools dictionary
            server_name: Server name(s)
            num_tasks: Number of tasks to generate
        """
        
        final_tasks = []
        task_index = 0
        
        while len(final_tasks) < num_tasks:
            retry_count = 0
            task_generated = False
            
            while retry_count < self.max_retries_per_task and not task_generated:
                try:
                    # Generate one detailed task
                    logger.info(f"Generating task {len(final_tasks)+1}/{num_tasks} for {server_name} (attempt {retry_count+1}/{self.max_retries_per_task})")
                    
                    detailed_task = await self._generate_single_detailed_task(
                        tools, server_name, task_index
                    )
                    
                    if not detailed_task:
                        logger.warning(f"Failed to generate detailed task, retry {retry_count+1}")
                        retry_count += 1
                        continue
                    
                    # Generate fuzzy version
                    fuzzy_version = await self._generate_fuzzy_version(
                        detailed_task['task_description'],
                        tools,
                        server_name
                    )
                    
                    if not fuzzy_version:
                        logger.warning(f"Failed to generate fuzzy version, retry {retry_count+1}")
                        retry_count += 1
                        continue
                    
                    # Create complete task
                    complete_task = {
                        'task_id': detailed_task['task_id'],
                        'task_description': detailed_task['task_description'],
                        'fuzzy_description': fuzzy_version,
                        'distraction_servers': self._select_distraction_servers(server_name),
                        'dependency_analysis': detailed_task.get('dependency_analysis', '')
                    }
                    
                    # Evaluate task quality
                    evaluation = await self.quality_evaluator.evaluate_task_quality(complete_task, tools)
                    
                    logger.info(f"Task quality scores - Solvability: {evaluation['solvability_score']:.1f}, Utility: {evaluation['utility_score']:.1f}")
                    
                    if self.quality_evaluator.meets_quality_threshold(evaluation):
                        # Task meets quality threshold
                        final_tasks.append(complete_task)
                        task_generated = True
                        logger.info(f"Task accepted! ({len(final_tasks)}/{num_tasks} completed)")
                    else:
                        # Task below threshold - discard and retry
                        logger.warning(f"Task below quality threshold (S:{evaluation['solvability_score']:.1f}, U:{evaluation['utility_score']:.1f})")
                        logger.warning(f"Solvability feedback: {evaluation.get('solvability_feedback', 'N/A')}")
                        logger.warning(f"Utility feedback: {evaluation.get('utility_feedback', 'N/A')}")
                        retry_count += 1
                        
                except Exception as e:
                    logger.error(f"Error in task generation attempt {retry_count+1}: {e}")
                    import traceback
                    logger.error(f"Full traceback: {traceback.format_exc()}")
                    retry_count += 1
            
            if not task_generated:
                logger.error(f"Failed to generate acceptable task after {self.max_retries_per_task} attempts")
                # Skip this task and continue
                
            task_index += 1
            
            # Safety check to prevent infinite loop
            if task_index > num_tasks * 10:
                logger.error("Too many attempts, stopping task generation")
                break
        
        logger.info(f"Successfully generated {len(final_tasks)}/{num_tasks} high-quality tasks for {server_name}")
        return final_tasks
    
    async def _generate_single_detailed_task(self,
                                           tools: Dict[str, Any],
                                           server_name: str,
                                           task_index: int) -> Optional[Dict[str, Any]]:
        """Generate a single detailed task"""
        
        tool_descriptions = self._format_tools(tools)
        
        # Special handling for OpenAPI server
        special_instructions = ""
        if "OpenAPI" in server_name or "openapi" in server_name.lower():
            special_instructions = """
CRITICAL REQUIREMENTS FOR OpenAPI EXPLORER TASKS:

AVAILABLE API SPEC IDENTIFIERS (Use these in your tasks):
- "openai" - OpenAI API specification
- "github" - GitHub API specification
- Use these identifiers when specifying which API spec to analyze

ABSOLUTELY FORBIDDEN:
- DO NOT create tasks that involve calling external APIs (Stripe, SendGrid, Slack, etc.)
- DO NOT generate tasks about "creating invoices", "sending emails", "posting messages"
- DO NOT reference external URLs or placeholder URLs like "api.example.com"
- DO NOT design tasks that perform real operations or create real data

REQUIRED - ONLY CREATE TASKS THAT:
- Analyze and audit API specifications (structure, completeness, consistency)
- Extract metadata about endpoints, methods, and operations
- Understand request/response schemas and data models
- Check security schemes and authentication requirements
- Review API documentation quality and coverage
- Identify deprecated operations or version differences
- Analyze parameter types, validation rules, and constraints
- Compare different API specifications
- Generate reports about API structure and capabilities

GOOD EXAMPLES: 
- "Audit the 'openai' API spec to identify all authentication methods and their security requirements"
- "Analyze the 'github' API spec to extract all endpoints related to repository management with their parameters"
BAD EXAMPLE: "Create invoices using Stripe API and send email notifications"

The task MUST be about ANALYZING/UNDERSTANDING the API spec, NOT USING the API!
"""
        
        prompt = f"""You are a task designer for testing AI agents with MCP tools.
{special_instructions}
STEP 1: ANALYZE AND CREATE TOOL DEPENDENCIES
Analyze these available tools and CREATE meaningful dependencies for your task scenario:

{tool_descriptions}

Consider both:
A) INHERENT dependencies (tool's natural input/output relationships)
   - Which tools naturally produce data others consume
   - Standard workflow patterns (search → fetch → analyze)
   
B) SCENARIO-BASED dependencies (create logical connections for your task), for example:
   - Tool A's result determines WHICH tool to use next
   - Tool B's output sets PARAMETERS for Tool C
   - Tool D validates or contradicts Tool E's findings
   - Parallel tools whose results must be COMBINED
   - Iterative loops where results trigger RE-ANALYSIS

Record your dependency analysis in a "dependency_analysis" field that describes:
- Key tool chains and data flow
- Critical decision points
- Parallel vs sequential requirements
- Cross-server dependencies (for multi-server tasks)

For multi-server tasks ({server_name}), create CROSS-SERVER dependencies:
- Server A data influences Server B queries
- Cross-validation between different data sources
- One server's limits trigger fallback to another

STEP 2: DESIGN ONE COMPLEX TASK
Based on your dependency analysis, create ONE task that:

- Create MAXIMUM complexity requiring massive tool calls
- Must use tools from all available servers
- Must consider inter-servers dependency if more than 1 server available
You may create the tasks with the following properties if suitable:
- Deep dependency chains where Tool B needs Tool A's output, Tool C needs B's output, etc.
- Multiple decision branches based on intermediate results
- Iterative refinement: initial findings lead to deeper investigation
- Cross-validation: use multiple tools to verify critical findings
- Data transformation: output from one tool needs processing before next tool
- Conditional workflows: if condition X, then workflow Y, else workflow Z

CRITICAL DATA REQUIREMENTS:
1. ALL tasks MUST be self-contained and executable WITHOUT any external dependencies
2. NEVER reference external resources like:
   - URLs (like "https://api.example.com" or any external API)
   - Local files (like "user-management.yaml" or "config.json")
   - Databases or external systems
   - "Our API", "our system", "our database"
3. ALL data must come from either:
   - The provided tools themselves (what they can generate/fetch/calculate)
   - Concrete values you specify in the task (numbers, names, parameters)
4. NEVER use vague references:
   - "user-provided parameters" or "user-specified"
   - "fetched from database" or "retrieved from external source"
   - "based on user preferences" or "according to input"
   - "specified location/value" or "to be determined"
5. ALWAYS provide concrete values:
   - Specific numbers (e.g., "analyze heat exchanger with inlet temp 80°C, outlet 60°C, flow rate 0.5 kg/s")
   - Named entities (e.g., "analyze weather in San Francisco" not "specified city")
   - For locations: Use city names, landmark names, or general areas, NOT specific street addresses
     - GOOD: "San Francisco", "Times Square", "Central Park area", "downtown Seattle"
     - BAD: "123 Main Street", "456 Park Avenue", specific house numbers or street addresses
   - Exact thresholds (e.g., "alert if efficiency drops below 85%" not "desired threshold")
   - ALWAYS USE relative dates/times (e.g., "next 7 days", "past 3 months", "upcoming week" not "January 2024" or "2024-01-15")
6. If the task involves analysis, provide ALL input data in the task description:
   - For calculations: provide all numbers, formulas, and units needed
   - For searches: provide specific search terms and criteria
   - For comparisons: provide specific items with their properties
   - For optimization: provide current values and target metrics

Requirements:
1. MUST require multiple tools in a specific sequence
2. Tool B should need output from Tool A (dependency chain)
3. Include decision points based on intermediate results
4. Be realistic and valuable for business/research purposes
5. Define expected analysis and output format
6. Task must be immediately executable - agent should never need to ask for more information
7. Task should be executable and solvable by using the provided tools. You need to pay attention to the function and the output of the provided tools.

Output ONLY a JSON object (not an array). ALWAYS USE relative dates/times (e.g., "next 7 days", "past 3 months", "upcoming week" not "January 2024" or "2024-01-15"):
{{
  "task_id": "task_{task_index:03d}",
  "task_description": "detailed task that leverages the identified tool dependencies",
  "dependency_analysis": "Your analysis from STEP 1 - describe the key dependencies, tool chains, decision points, and data flow patterns that this task requires"
}}
Focus on creating a task that CANNOT be completed without understanding tool dependencies."""

        try:
            response = await self.llm.get_completion(
                system_prompt="You are an expert at creating detailed benchmark tasks with deep understanding of tool dependencies.",
                user_prompt=prompt,
                max_tokens=10000
            )
            
            # Parse single task response
            task = self._parse_single_task_response(response)
            
            if task:
                # Generate task_id in the correct format
                server_id = server_name.lower().replace(' ', '_').replace('+', '_')
                task['task_id'] = f"{server_id}_{task_index:03d}"
                return task
            else:
                logger.warning(f"Failed to parse task from response")
                return None
                
        except Exception as e:
            logger.error(f"Error generating single task: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return None
    
    def _select_distraction_servers(self, server_name: str, count: int = 10) -> List[str]:
        """Select random distraction servers, excluding the current server(s)"""
        
        # Extract server names from multi-server combinations
        if '+' in server_name:
            active_servers = server_name.split('+')
        else:
            active_servers = [server_name]
        
        # Normalize server names for comparison
        active_servers_normalized = [s.lower().replace(' ', '_').replace('-', '_') for s in active_servers]
        
        # Filter out active servers from the pool
        available_distractions = []
        for server in self.distraction_server_pool:
            server_normalized = server.lower().replace(' ', '_').replace('-', '_')
            # Check if this server is not in active servers
            is_active = False
            for active in active_servers_normalized:
                if active in server_normalized or server_normalized in active:
                    is_active = True
                    break
            if not is_active:
                available_distractions.append(server)
        
        # Randomly select distraction servers
        selected_count = min(count, len(available_distractions))
        selected = random.sample(available_distractions, selected_count)
        
        return selected
    
    
    async def _generate_fuzzy_version(self, 
                                     detailed_task: str,
                                     tools: Dict[str, Any],
                                     server_name: str = None) -> Optional[str]:
        """Stage 2: Generate fuzzy version with evidence requirements"""
        
        # Check if this involves calculation/computation tools
        calculation_servers = ['scientific_computing', 'math_mcp', 'unit_converter', 'medical_calculator', 'medcalc']
        
        is_calculation_task = False
        if server_name:
            server_name_normalized = server_name.lower().replace(' ', '_').replace('-', '_')
            is_calculation_task = any(calc_name in server_name_normalized for calc_name in calculation_servers)
        
        # Also check tool names for calculation keywords
        if not is_calculation_task and tools:
            tool_names_str = ' '.join(tools.keys()).lower()
            calc_keywords = ['calculat', 'compute', 'math', 'formula', 'equation', 'convert']
            is_calculation_task = any(keyword in tool_names_str for keyword in calc_keywords)
        
        # Add special requirements for calculation tasks
        calculation_requirements = ""
        if is_calculation_task:
            calculation_requirements = """

CRITICAL FOR CALCULATION/COMPUTATION TASKS:
- MUST preserve ALL specific numerical values including vector and matrix from the original task
- MUST keep concrete inputs like "156.7, 234.9, and 89.3" in the fuzzy version
- MUST maintain exact measurements like "45.6 meters" even while making the request conversational
- MUST retain precise parameters like "weight=75kg, height=1.82m"
- The fuzzy version should still contain the actual numbers, just phrased more naturally
- Example: "Calculate sqrt(144) and add to 25.5" → "I need to figure out what the square root of 144 is and then add 25.5 to it"
- DO NOT replace specific numbers with vague terms like "some values" or "certain measurements"
"""
        
        prompt = f"""Convert this detailed task into a NATURAL, CONVERSATIONAL USER REQUEST that truly tests the agent's reasoning ability.

Original detailed task:
{detailed_task}

Available tools: {len(tools)} tools (but don't mention them in the fuzzy version)

CRITICAL: CREATE A GENUINELY NATURAL REQUEST

ABSOLUTELY FORBIDDEN:
- ANY structured language that looks like a task description
- Phrases like "I need to analyze", "I want to compare", "Please evaluate"
- ANY specific server/platform names (arXiv, PubMed, Yahoo Finance, Google Maps, etc.)
- ANY tool names or technical implementation details
- Lists, enumerations, or step-by-step instructions
- Formal task language ("perform", "conduct", "execute", "implement")

INSTEAD, CREATE A NATURAL CONVERSATION:
- Start with context or a problem the user is facing
- Use conversational openers: "I'm trying to figure out...", "Been wondering about...", "Got a situation here..."
- Include uncertainty: "not sure if", "maybe", "possibly", "might be"
- Add personal context: "for my project", "my boss asked", "I'm curious about"
- Express the need through a story or scenario, not a task list

HIDE THE TASK STRUCTURE COMPLETELY:
Don't say: "I need to analyze financial metrics for AAPL, GOOGL, and MSFT"
Say instead: "I've been thinking about rebalancing my portfolio and I'm curious how tech giants like AAPL, GOOGL, and MSFT have been doing lately. Which one would you say looks strongest right now?"

Don't say: "Search for recent papers on CRISPR and summarize the key findings"
Say instead: "I'm giving a presentation next week about gene editing. What's the latest buzz around CRISPR? Any breakthrough discoveries I should know about?"

Don't say: "Calculate the thermal efficiency and optimize the heat exchanger parameters"
Say instead: "We've got this heat exchanger running at 80°C inlet, 60°C outlet with 0.5 kg/s flow. It doesn't seem very efficient to me. Can you help me figure out what's going on and maybe how to improve it?"

PRESERVE CRITICAL DATA NATURALLY:
- Embed specific values conversationally: "around 150 or so", "somewhere near San Francisco"
- Use approximate language when appropriate: "roughly", "about", "somewhere between"
- Keep exact values only when truly necessary (calculations, IDs, etc.)
{calculation_requirements}

MAKE IT SOUND LIKE A REAL PERSON:
- Use contractions: "I'm", "don't", "can't", "what's"
- Include filler words sparingly: "actually", "basically", "you know"
- Show emotion or urgency when appropriate: "really need to know", "been bugging me"
- Ask questions naturally: "What do you think?", "Does that make sense?", "Am I overthinking this?"

EXAMPLES OF NATURAL FUZZY DESCRIPTIONS:

Example 1 (Finance):
"So I've been watching my tech stocks lately and honestly, I'm not sure if I should hold or sell. AAPL, GOOGL, and MSFT make up most of my portfolio. With everything going on in the market, which one do you think has the best outlook? I'm particularly worried about their debt levels and cash flow situation. Need some real data to back up any decision here, not just gut feelings."

Example 2 (Research):
"I'm preparing for a journal club presentation and everyone's been talking about these new CRISPR developments. What's actually new in the past few months? I keep hearing about off-target effects being solved but can't find solid evidence. Would really appreciate concrete findings from recent studies, not just hype."

Example 3 (Technical):
"We're having issues with our heat exchanger setup - running at 80°C in, 60°C out, flow rate's about 0.5 kg/s. My manager thinks we're wasting energy but I need to prove it with actual numbers. Can you work out what our current efficiency is and maybe suggest what parameters we should tweak? Need solid calculations to convince them to approve changes."

CRITICAL: End naturally with evidence requirements woven into the conversation:
Instead of: "Please provide evidence-based analysis with concrete data"
Say: "I really need actual data on this - can't go to my boss with just opinions. Whatever you find, make sure it's backed up by real numbers or solid sources, okay?"

ALWAYS USE relative dates/times (e.g., "next 7 days", "past 3 months", "upcoming week" not "January 2024" or "2024-01-15")

Return ONLY the natural, conversational fuzzy description - make it sound like a real person asking for help, not a robot executing a task."""

        try:
            response = await self.llm.get_completion(
                system_prompt="You create natural user requests that require evidence-based responses.",
                user_prompt=prompt,
                max_tokens=10000
            )
            
            fuzzy = response.strip()
            
            # Validate fuzzy has evidence requirement
            fuzzy_lower = fuzzy.lower()
            has_evidence = any(word in fuzzy_lower for word in 
                             ['evidence', 'concrete', 'verifiable', 'backed by', 'support', 'obtain', 'compute'])
            
            if not has_evidence:
                # Add evidence requirement if missing
                fuzzy += "\n\nPlease ensure all findings are supported by concrete data and verifiable sources. I need specific numbers and evidence, not generalizations."
            
            # Check for step enumeration patterns (warn but don't reject)
            step_patterns = [
                r'\bstep\s+\d+\b', r'\b\d+\.\s+', r'\bfirst\s+.*then\s+.*finally\b',
                r'\bphase\s+\d+\b', r'\btask\s+\d+\b'
            ]
            import re
            for pattern in step_patterns:
                if re.search(pattern, fuzzy_lower):
                    logger.warning(f"Fuzzy description may contain step enumeration: pattern '{pattern}' found")
            
            return fuzzy
            
        except Exception as e:
            logger.error(f"Error generating fuzzy version: {e}")
            return None
    
    def _format_tools(self, tools: Dict[str, Any]) -> str:
        """Format tool descriptions for prompt"""
        formatted = ""
        tool_count = 0
        for tool_name, tool_info in tools.items():
            if tool_count >= 30:  # Limit to first 30 tools
                formatted += f"\n... and {len(tools) - 30} more tools\n"
                break
            
            if tool_info is None:
                logger.error(f"Tool {tool_name} has None info! Tools dict keys: {list(tools.keys())[:10]}")
                continue
            
            formatted += f"\nTool: `{tool_name}` (Server: {tool_info.get('server', 'unknown')})\n"
            formatted += f"  Description: {tool_info.get('description', 'No description')}\n"
            
            input_schema = tool_info.get('input_schema')
            if input_schema:
                schema_str = json.dumps(input_schema, indent=2)
                formatted += f"  Input Schema:\n```json\n{schema_str}\n```\n"
            
            tool_count += 1
        
        return formatted
    
    def _parse_single_task_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse LLM response to extract a single task JSON object"""
        try:
            # Try direct JSON parsing
            task = json.loads(response)
            if isinstance(task, dict) and 'task_description' in task:
                # Ensure dependency_analysis field is present
                if 'dependency_analysis' not in task:
                    logger.warning("Missing dependency_analysis field in generated task")
                return task
        except:
            pass
        
        # Try to extract JSON from various formats
        import re
        
        # Try ```json block
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            try:
                task = json.loads(json_match.group(1))
                if isinstance(task, dict) and 'task_description' in task:
                    return task
            except:
                pass
        
        # Try plain code block
        json_match = re.search(r'```\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            try:
                task = json.loads(json_match.group(1))
                if isinstance(task, dict) and 'task_description' in task:
                    return task
            except:
                pass
        
        # Try to find any JSON object with task_description
        json_match = re.search(r'\{[^{}]*"task_description"[^{}]*\}', response, re.DOTALL)
        if json_match:
            try:
                task = json.loads(json_match.group())
                if isinstance(task, dict) and 'task_description' in task:
                    return task
            except:
                pass
        
        logger.error("Failed to parse single task from LLM response")
        return None
    
    def _parse_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response to extract JSON array (kept for compatibility)"""
        try:
            return json.loads(response)
        except:
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
        
        logger.error("Failed to parse LLM response as JSON")
        return []
