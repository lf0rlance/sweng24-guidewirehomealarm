import unittest

from db.access_control import permissions_for_level


class TestPermissionsForLevel(unittest.TestCase):
    def test_owner_has_full_permissions(self):
        p = permissions_for_level("owner")
        self.assertTrue(p["can_arm"])
        self.assertTrue(p["can_disarm"])
        self.assertTrue(p["can_view_events"])
        self.assertTrue(p["can_receive_notifications"])
        self.assertTrue(p["can_manage_users"])

    def test_child_cannot_view_events_or_notifications(self):
        p = permissions_for_level("child")
        self.assertTrue(p["can_arm"])
        self.assertTrue(p["can_disarm"])
        self.assertFalse(p["can_view_events"])
        self.assertFalse(p["can_receive_notifications"])
        self.assertFalse(p["can_manage_users"])

    def test_arm_only_cannot_disarm(self):
        p = permissions_for_level("arm_only")
        self.assertTrue(p["can_arm"])
        self.assertFalse(p["can_disarm"])
        self.assertFalse(p["can_view_events"])
        self.assertFalse(p["can_receive_notifications"])

    def test_unknown_is_safe_default(self):
        p = permissions_for_level("some_new_role")
        self.assertFalse(any(p.values()))

