import json
import unittest

from benchmark.evaluator import LLMJudge, TaskEvaluator
from benchmark.score_normalization import normalize_raw_llm_judge_scores


class StubLLM:
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


class ScoreNormalizationTest(unittest.TestCase):
    def test_normalizes_raw_llm_judge_scores_to_zero_one_scale(self):
        normalized = normalize_raw_llm_judge_scores({
            "task_fulfillment": 1,
            "grounding": 8.5,
            "tool_appropriateness": 10,
            "parameter_accuracy": 0,
            "input_schema_compliance": 0.95,
            "task_fulfillment_reasoning": "raw judge score",
        })

        self.assertEqual(normalized["task_fulfillment"], 0.1)
        self.assertEqual(normalized["grounding"], 0.85)
        self.assertEqual(normalized["tool_appropriateness"], 1.0)
        self.assertEqual(normalized["parameter_accuracy"], 0)
        self.assertEqual(normalized["input_schema_compliance"], 0.95)
        self.assertEqual(normalized["task_fulfillment_reasoning"], "raw judge score")

    def test_stability_average_scores_are_normalized_before_aggregation(self):
        judge = LLMJudge(llm_provider=None)

        averaged = judge._calculate_average_scores([
            {
                "task_fulfillment": 8,
                "grounding": 6,
                "tool_appropriateness": 10,
                "parameter_accuracy": 4,
                "dependency_awareness": 7,
                "parallelism_and_efficiency": 3,
                "task_completion_analysis": "first",
            },
            {
                "task_fulfillment": 6,
                "grounding": 4,
                "tool_appropriateness": 8,
                "parameter_accuracy": 6,
                "dependency_awareness": 5,
                "parallelism_and_efficiency": 5,
                "task_completion_analysis": "second",
            },
        ])

        self.assertAlmostEqual(averaged["task_fulfillment"], 0.7)
        self.assertAlmostEqual(averaged["grounding"], 0.5)
        self.assertAlmostEqual(averaged["tool_appropriateness"], 0.9)
        self.assertAlmostEqual(averaged["parameter_accuracy"], 0.5)
        self.assertAlmostEqual(averaged["dependency_awareness"], 0.6)
        self.assertAlmostEqual(averaged["parallelism_and_efficiency"], 0.4)
        self.assertAlmostEqual(averaged["task_completion_score"], 0.6)
        self.assertAlmostEqual(averaged["tool_selection_score"], 0.7)
        self.assertAlmostEqual(
            averaged["planning_effectiveness_and_efficiency_score"],
            0.5,
        )
        self.assertEqual(averaged["task_completion_analysis"], "first")


class TaskEvaluatorScoreNormalizationTest(unittest.IsolatedAsyncioTestCase):
    async def test_task_evaluator_returns_normalized_llm_judge_scores(self):
        evaluator = TaskEvaluator(StubLLM())

        evaluation = await evaluator.evaluate(
            task="test task",
            execution_results=[],
            final_solution="done",
            total_rounds=1,
            available_tools={},
            planning_json_compliance=1.0,
        )

        self.assertAlmostEqual(evaluation["task_fulfillment"], 0.8)
        self.assertAlmostEqual(evaluation["grounding"], 0.6)
        self.assertAlmostEqual(evaluation["tool_appropriateness"], 1.0)
        self.assertAlmostEqual(evaluation["parameter_accuracy"], 0.4)
        self.assertAlmostEqual(evaluation["dependency_awareness"], 0.7)
        self.assertAlmostEqual(evaluation["parallelism_and_efficiency"], 0.3)
        self.assertAlmostEqual(evaluation["task_completion_score"], 0.7)
        self.assertAlmostEqual(evaluation["tool_selection_score"], 0.7)
        self.assertAlmostEqual(
            evaluation["planning_effectiveness_and_efficiency_score"],
            0.5,
        )
        self.assertIsNone(evaluation["input_schema_compliance"])


if __name__ == "__main__":
    unittest.main()
