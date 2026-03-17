import unittest

from localization_adapter_pkg.core import build_status_payload, choose_active_source


class LocalizationCoreTest(unittest.TestCase):
    def test_primary_is_selected_when_recent(self) -> None:
        self.assertEqual(
            choose_active_source(
                primary_age_s=0.2,
                fallback_available=True,
                primary_timeout_s=0.75,
            ),
            "primary",
        )

    def test_fallback_is_selected_when_primary_is_stale(self) -> None:
        self.assertEqual(
            choose_active_source(
                primary_age_s=1.2,
                fallback_available=True,
                primary_timeout_s=0.75,
            ),
            "fallback",
        )

    def test_status_payload_contains_active_source_and_topics(self) -> None:
        payload = build_status_payload(
            active_source="fallback",
            primary_topic="/visual_slam/tracking/odometry",
            fallback_topic="/agentslam/gt/odom",
            output_topic="/agentslam/localization/odom",
            primary_messages=0,
            fallback_messages=3,
            primary_age_s=None,
        )
        self.assertEqual(payload["active_source"], "fallback")
        self.assertEqual(payload["fallback_messages"], 3)
        self.assertEqual(payload["output_topic"], "/agentslam/localization/odom")
