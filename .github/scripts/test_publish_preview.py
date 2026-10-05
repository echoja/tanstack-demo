import base64
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import Mock


spec = importlib.util.spec_from_file_location(
    "publish_preview", Path(__file__).with_name("publish-preview.py")
)
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)

HEAD = "a" * 40
PREVIOUS = "b" * 40
OPEN_PR = {"state": "open", "head": {"sha": HEAD}}


def record(head_sha):
    return {
        "sha": "file-blob-sha",
        "content": base64.b64encode(
            json.dumps({"publishedSha": head_sha}).encode()
        ).decode(),
    }


class PublishPreviewTests(unittest.TestCase):
    def publish(self, request, pause=None):
        return publisher.publish_preview(
            "echoja/tanstack-demo", "18", HEAD, request, pause or Mock()
        )

    def test_first_success_creates_record(self):
        request = Mock(side_effect=[OPEN_PR, publisher.ApiError("HTTP 404"), {}])
        self.assertTrue(self.publish(request))
        payload = request.call_args.args[1]
        self.assertEqual(payload["branch"], "main")
        self.assertNotIn("sha", payload)
        self.assertEqual(
            json.loads(base64.b64decode(payload["content"])), {"publishedSha": HEAD}
        )

    def test_success_updates_previous_image_with_blob_precondition(self):
        request = Mock(side_effect=[OPEN_PR, record(PREVIOUS), {}])
        self.assertTrue(self.publish(request))
        self.assertEqual(request.call_args.args[1]["sha"], "file-blob-sha")

    def test_superseded_or_closed_build_leaves_existing_record_alone(self):
        for pr in [
            {"state": "closed", "head": {"sha": HEAD}},
            {"state": "open", "head": {"sha": PREVIOUS}},
        ]:
            with self.subTest(pr=pr):
                request = Mock(return_value=pr)
                self.assertFalse(self.publish(request))
                self.assertEqual(request.call_count, 1)

    def test_rerun_does_not_create_another_commit(self):
        request = Mock(side_effect=[OPEN_PR, record(HEAD)])
        self.assertTrue(self.publish(request))
        self.assertEqual(request.call_count, 2)

    def test_conflict_rechecks_pr_and_reloads_record(self):
        request = Mock(side_effect=[
            OPEN_PR, record(PREVIOUS), publisher.ApiError("HTTP 409"),
            OPEN_PR, record(PREVIOUS), {},
        ])
        pause = Mock()
        self.assertTrue(self.publish(request, pause))
        self.assertEqual(request.call_count, 6)
        pause.assert_called_once_with(1)

    def test_superseded_during_conflict_retry_cannot_overwrite_newer_record(self):
        request = Mock(side_effect=[
            OPEN_PR, record(PREVIOUS), publisher.ApiError("HTTP 409"),
            {"state": "open", "head": {"sha": PREVIOUS}},
        ])
        self.assertFalse(self.publish(request))
        self.assertEqual(request.call_count, 4)

    def test_authentication_and_write_errors_fail_publication(self):
        for results in [
            [OPEN_PR, publisher.ApiError("HTTP 403")],
            [OPEN_PR, record(PREVIOUS), publisher.ApiError("HTTP 500")],
        ]:
            with self.subTest(results=results):
                with self.assertRaises(publisher.ApiError):
                    self.publish(Mock(side_effect=results))

    def test_conflict_retries_are_bounded(self):
        request = Mock(side_effect=[
            OPEN_PR, record(PREVIOUS), publisher.ApiError("HTTP 409")
        ] * 5)
        with self.assertRaises(publisher.ApiError):
            self.publish(request)
        self.assertEqual(request.call_count, 15)

    def test_invalid_identifiers_cannot_write_arbitrary_paths(self):
        for pr, sha in [("../18", HEAD), ("18", "short-sha")]:
            request = Mock()
            with self.assertRaises(ValueError):
                publisher.publish_preview("echoja/tanstack-demo", pr, sha, request)
            request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
