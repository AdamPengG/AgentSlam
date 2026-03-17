import unittest

from sim_bridge_pkg.fixture_io import load_bridge_fixture, quaternion_from_yaw


class FixtureIoTest(unittest.TestCase):
    def test_load_bridge_fixture(self) -> None:
        fixture = load_bridge_fixture("fixtures/semantic_mapping/office_nova_replay_scene.json")
        self.assertEqual(len(fixture.frames), 3)
        self.assertEqual(fixture.frames[0].detections[0].label, "chair")

    def test_quaternion_from_yaw(self) -> None:
        qx, qy, qz, qw = quaternion_from_yaw(0.0)
        self.assertEqual((qx, qy), (0.0, 0.0))
        self.assertAlmostEqual(qz, 0.0)
        self.assertAlmostEqual(qw, 1.0)


if __name__ == "__main__":
    unittest.main()
