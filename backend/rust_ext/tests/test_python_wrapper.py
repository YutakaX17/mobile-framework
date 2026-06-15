import json
import re
import unittest

from mobile_framework_rust import (
    canonicalize_json,
    diff_app_json,
    extension_version,
    hash_config_json,
    hash_package_json,
    health_check,
    merge_sync_json,
)


class PythonWrapperTest(unittest.TestCase):
    def test_health_and_version_exports(self) -> None:
        self.assertEqual(health_check(), "ok")
        self.assertRegex(extension_version(), r"^\d+\.\d+\.\d+")

    def test_canonicalize_json_export(self) -> None:
        self.assertEqual(canonicalize_json('{"b":2,"a":1}'), '{"a":1,"b":2}')

    def test_hash_exports(self) -> None:
        digest_pattern = re.compile(r"^sha256:[a-f0-9]{64}$")
        self.assertRegex(hash_config_json('{"b":2,"a":1}'), digest_pattern)
        self.assertRegex(hash_package_json('{"package_id":"pkg","modules":[]}'), digest_pattern)

    def test_diff_app_json_export(self) -> None:
        diff = json.loads(
            diff_app_json(
                '{"app_id":"field_ops","name":"Old"}',
                '{"app_id":"field_ops","name":"New"}',
            )
        )
        self.assertEqual(
            diff,
            [
                {
                    "change_type": "changed",
                    "path": "$.name",
                    "old": "Old",
                    "new": "New",
                }
            ],
        )

    def test_merge_sync_json_export(self) -> None:
        result = json.loads(
            merge_sync_json(
                '{"status":"draft","version":1}',
                '{"status":"local","version":1}',
                '{"status":"draft","version":2}',
            )
        )
        self.assertEqual(result["status"], "merged")
        self.assertEqual(result["merged"], {"status": "local", "version": 2})
        self.assertEqual(result["conflicts"], [])


if __name__ == "__main__":
    unittest.main()
