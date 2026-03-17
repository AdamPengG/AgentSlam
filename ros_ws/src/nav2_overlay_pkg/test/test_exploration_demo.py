import unittest

from nav2_overlay_pkg.exploration_demo import build_semantic_gain_route, simulate_semantic_exploration


class ExplorationDemoTest(unittest.TestCase):
    def test_route_prefers_new_semantics(self) -> None:
        payload = simulate_semantic_exploration(
            fixture_path="fixtures/semantic_mapping/exploration_gt_pose_scene.json",
            output_map_path="/tmp/agentslam_exploration_map.json",
            progress_output_path="/tmp/agentslam_exploration_progress.json",
            query_output_dir="/tmp/agentslam_exploration_queries",
            query_labels=["chair", "cabinet"],
            merge_distance_m=0.8,
        )
        self.assertEqual(payload["mode"], "offline_semantic_exploration")
        self.assertEqual(len(payload["steps"]), 4)
        self.assertGreater(payload["final_map_summary"]["object_count"], 2)

    def test_build_route(self) -> None:
        from semantic_mapper_pkg.io import load_fixture

        route = build_semantic_gain_route(
            load_fixture("fixtures/semantic_mapping/exploration_gt_pose_scene.json")
        )
        self.assertEqual(route[0]["frame"].frame_id, "frame_000")
        self.assertEqual(len(route), 4)


if __name__ == "__main__":
    unittest.main()
