import unittest

from semantic_mapper_pkg.models import CameraIntrinsics, Pose2D, SemanticDetection

from nav2_overlay_pkg.geometry import GeometricMapBuilder


class GeometryBuilderTest(unittest.TestCase):
    def test_builder_exports_occupied_and_free_cells(self) -> None:
        builder = GeometricMapBuilder(resolution_m=0.5)
        intrinsics = CameraIntrinsics(fx=525.0, fy=525.0, cx=320.0, cy=240.0)
        pose = Pose2D(x=0.0, y=0.0, yaw=0.0, z=0.0)
        detections = [
            SemanticDetection(
                label="chair",
                pixel_x=320.0,
                pixel_y=240.0,
                depth_m=2.0,
                confidence=0.95,
            )
        ]
        builder.add_observation(
            frame_id="frame_000",
            pose=pose,
            intrinsics=intrinsics,
            detections=detections,
        )

        payload = builder.export()
        self.assertEqual(payload["occupied_count"], 1)
        self.assertGreaterEqual(payload["free_count"], 1)
        self.assertEqual(len(payload["path"]), 1)

    def test_builder_tracks_multiple_observed_points(self) -> None:
        builder = GeometricMapBuilder(resolution_m=0.25)
        intrinsics = CameraIntrinsics(fx=525.0, fy=525.0, cx=320.0, cy=240.0)
        builder.add_observation(
            frame_id="frame_000",
            pose=Pose2D(x=0.0, y=0.0, yaw=0.0, z=0.0),
            intrinsics=intrinsics,
            detections=[
                SemanticDetection("chair", 320.0, 240.0, 2.0, 0.9),
                SemanticDetection("desk", 420.0, 240.0, 3.0, 0.88),
            ],
        )
        payload = builder.export()
        labels = {point["label"] for point in payload["observed_points"]}
        self.assertEqual(labels, {"chair", "desk"})
