import tempfile
import unittest
from pathlib import Path

from benchmark.trajectory_writer import build_trajectory_path, write_task_trajectory


class TrajectoryWriterTest(unittest.TestCase):
    def test_build_trajectory_path_sanitizes_model_and_task_id(self):
        path = build_trajectory_path(
            "/tmp/trajectories",
            model_name="openai/gpt-oss:20b",
            task_id="openapi explorer/000",
        )

        self.assertEqual(
            path,
            Path("/tmp/trajectories/openai_gpt-oss_20b/openapi_explorer_000.txt"),
        )

    def test_write_task_trajectory_creates_parent_dir_and_content(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = write_task_trajectory(
                output_dir=tmp_dir,
                task_id="openapi_explorer_000",
                model_name="gpt-oss-20b",
                server_name="openapi_explorer",
                task_description="Explore the API.",
                trajectory_text="Total rounds: 2; Tools executed: 1",
            )

            written = Path(path)
            self.assertTrue(written.exists())
            self.assertEqual(
                written,
                Path(tmp_dir) / "gpt-oss-20b" / "openapi_explorer_000.txt",
            )

            content = written.read_text(encoding="utf-8")
            self.assertIn("Task ID: openapi_explorer_000", content)
            self.assertIn("Model: gpt-oss-20b", content)
            self.assertIn("Server: openapi_explorer", content)
            self.assertIn("Task Description:", content)
            self.assertIn("Explore the API.", content)
            self.assertIn("--- TRAJECTORY ---", content)
            self.assertIn("Total rounds: 2; Tools executed: 1", content)


if __name__ == "__main__":
    unittest.main()
