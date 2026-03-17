import unittest

from semantic_mapper_pkg.runtime import parse_detection_envelope, query_exported_map, slugify_label


class RuntimeContractTest(unittest.TestCase):
    def test_parse_detection_envelope(self) -> None:
        envelope = parse_detection_envelope(
            """
            {
              "frame_id": "frame_002",
              "source_mode": "bag_replay",
              "detections": [
                {
                  "label": "chair",
                  "pixel_x": 320.0,
                  "pixel_y": 240.0,
                  "depth_m": 1.8,
                  "confidence": 0.97
                }
              ]
            }
            """
        )
        self.assertEqual(envelope.frame_id, "frame_002")
        self.assertEqual(envelope.source_mode, "bag_replay")
        self.assertEqual(len(envelope.detections), 1)
        self.assertEqual(envelope.detections[0].label, "chair")

    def test_query_exported_map(self) -> None:
        payload = {
            "objects": [
                {
                    "label": "chair",
                    "object_id": "chair-1",
                    "position": {"x": 2.0, "y": 0.0, "z": 0.0},
                    "observation_count": 2,
                },
                {
                    "label": "cabinet",
                    "object_id": "cabinet-1",
                    "position": {"x": 5.0, "y": 5.0, "z": 0.0},
                    "observation_count": 1,
                },
            ]
        }
        response = query_exported_map(payload, "cab")
        self.assertEqual(response["match_count"], 1)
        self.assertEqual(response["matches"][0]["label"], "cabinet")

        nearby = query_exported_map(
            payload,
            "a",
            near_x=2.0,
            near_y=0.0,
            radius_m=0.5,
            min_observations=2,
        )
        self.assertEqual(nearby["match_count"], 1)
        self.assertEqual(nearby["matches"][0]["label"], "chair")
        self.assertEqual(nearby["matches"][0]["distance_m"], 0.0)

    def test_slugify_label(self) -> None:
        self.assertEqual(slugify_label("Desk / Cabinet"), "desk_cabinet")


if __name__ == "__main__":
    unittest.main()
