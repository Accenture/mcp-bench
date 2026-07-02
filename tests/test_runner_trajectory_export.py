import json
import tempfile
import unittest
from pathlib import Path

from benchmark.runner import BenchmarkRunner


class StubJudgeProvider:
    async def get_completion(self, system_prompt, user_prompt, max_tokens):
        return json.dumps({
            "task_fulfillment_reasoning": "ok",
            "grounding_reasoning": "ok",
            "tool_appropriateness_reasoning": "ok",
            "parameter_accuracy_reasoning": "ok",
            "dependency_awareness_reasoning": "ok",
            "parallelism_efficiency_reasoning": "ok",
            "task_fulfillment": 8,
            "grounding": 6,
            "tool_appropriateness": 10,
            "parameter_accuracy": 4,
            "dependency_awareness": 7,
            "parallelism_and_efficiency": 3,
        })

    def clean_and_parse_json(self, raw_json):
        return json.loads(raw_json)


class RunnerTrajectoryExportTest(unittest.IsolatedAsyncioTestCase):
    async def test_evaluate_task_result_writes_trajectory_when_output_dir_is_set(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            runner = BenchmarkRunner(
                judge_provider=StubJudgeProvider(),
                trajectory_output_dir=tmp_dir,
            )

            result = await runner._evaluate_task_result(
                task_execution_info={
                    "task_id": "openapi_explorer_000",
                    "task_description": "Explore the API.",
                    "concrete_task_description": "Explore the API.",
                    "server_name": "openapi_explorer",
                },
                execution_result={
                    "result": {
                        "execution_results": [
                            {
                                "tool": "openapi_search",
                                "success": True,
                                "parameters": {"query": "pets"},
                            }
                        ],
                        "solution": "Done",
                        "total_rounds": 2,
                        "available_tools": {
                            "openapi_search": {
                                "server": "openapi_explorer",
                                "description": "Search OpenAPI specs",
                            }
                        },
                        "planning_json_compliance": 1.0,
                        "accumulated_information": "Round 1 called openapi_search.",
                    },
                    "task_execution_start_time": 0,
                    "execution_time": 1.0,
                    "agent_execution_time": 0.5,
                },
                model_name="gpt-oss-20b",
                server_name="openapi_explorer",
            )

            trajectory_path = Path(result["trajectory_file"])
            self.assertTrue(trajectory_path.exists())
            self.assertEqual(
                trajectory_path,
                Path(tmp_dir) / "gpt-oss-20b" / "openapi_explorer_000.txt",
            )

            content = trajectory_path.read_text(encoding="utf-8")
            self.assertIn("Task ID: openapi_explorer_000", content)
            self.assertIn("Model: gpt-oss-20b", content)
            self.assertIn("Server: openapi_explorer", content)
            self.assertIn("Total rounds: 2", content)
            self.assertIn("Tools executed: 1", content)
            self.assertIn("Round 1 called openapi_search.", content)


if __name__ == "__main__":
    unittest.main()
