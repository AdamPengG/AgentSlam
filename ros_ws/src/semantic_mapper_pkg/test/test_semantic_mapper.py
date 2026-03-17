import tempfile
import unittest
from pathlib import Path

from semantic_mapper_pkg.io import load_fixture
from semantic_mapper_pkg.map_builder import SemanticMapBuilder


class SemanticMapperTest(unittest.TestCase):
    def test_fixture_fusion_and_query(self) -> None:
        frames = load_fixture("fixtures/semantic_mapping/synthetic_gt_pose_scene.json")
        builder = SemanticMapBuilder(merge_distance_m=0.8)

        for frame in frames:
            builder.add_frame(frame)

        exported = builder.export()
        self.assertEqual(exported["object_count"], 2)
        self.assertEqual(exported["labels"]["chair"], 1)
        self.assertEqual(exported["labels"]["table"], 1)

        chair_query = builder.query("chair")
        self.assertEqual(chair_query["match_count"], 1)
        self.assertEqual(chair_query["matches"][0]["observation_count"], 2)

        nearby_query = builder.query(
            "a",
            near_x=2.0,
            near_y=0.0,
            radius_m=0.35,
            min_observations=2,
        )
        self.assertEqual(nearby_query["match_count"], 1)
        self.assertEqual(nearby_query["matches"][0]["label"], "chair")
        self.assertLess(nearby_query["matches"][0]["distance_m"], 0.05)

        limited_query = builder.query("a", limit=1)
        self.assertEqual(limited_query["match_count"], 2)
        self.assertEqual(limited_query["returned_match_count"], 1)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "semantic_map.json"
            builder.export_to_path(output_path)
            self.assertTrue(output_path.exists())


if __name__ == "__main__":
    unittest.main()
