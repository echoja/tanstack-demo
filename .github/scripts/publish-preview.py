"""Record a published PR image in infra without advancing to failed builds."""

import base64
import json
import os
import re
import subprocess
import time


class ApiError(RuntimeError):
    pass


def api(endpoint, payload=None, source=False):
    env = os.environ.copy()
    if source:
        env["GH_TOKEN"] = env["GH_SOURCE_TOKEN"]
    command = ["gh", "api", endpoint]
    if payload is not None:
        command += ["--method", "PUT", "--input", "-"]
    result = subprocess.run(
        command,
        input=json.dumps(payload) if payload is not None else None,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    if result.returncode:
        raise ApiError(result.stderr)
    return json.loads(result.stdout)


def publish_preview(source_repo, pr_number, head_sha, request=api, pause=time.sleep):
    if not re.fullmatch(r"[1-9][0-9]*", pr_number):
        raise ValueError("PR number must be a positive integer")
    if not re.fullmatch(r"[0-9a-f]{40}", head_sha):
        raise ValueError("Image SHA must be a full commit SHA")

    endpoint = f"repos/echoja/infra/contents/previews/tanstack-demo/{pr_number}.json"
    content = json.dumps({"publishedSha": head_sha}, indent=2) + "\n"
    for attempt in range(5):
        pr = request(f"repos/{source_repo}/pulls/{pr_number}", source=True)
        if pr["state"] != "open" or pr["head"]["sha"] != head_sha:
            print("Skipping a closed PR or superseded build")
            return False

        try:
            existing = request(endpoint + "?ref=main")
        except ApiError as error:
            if "HTTP 404" not in str(error):
                raise
            existing = None

        if existing:
            previous = json.loads(base64.b64decode(existing["content"]))
            if previous["publishedSha"] == head_sha:
                print("Published image is already recorded")
                return True

        payload = {
            "message": f"Update TanStack Demo preview #{pr_number} to sha-{head_sha}",
            "branch": "main",
            "content": base64.b64encode(content.encode()).decode(),
        }
        if existing:
            payload["sha"] = existing["sha"]
        try:
            request(endpoint, payload)
            print(f"Recorded published image for preview #{pr_number}")
            return True
        except ApiError as error:
            # Another infra commit may have landed between reading and writing.
            if "HTTP 409" not in str(error) or attempt == 4:
                raise
            pause(2 ** attempt)
    raise RuntimeError("Preview publication retries exhausted")


if __name__ == "__main__":
    published = publish_preview(
        os.environ["GITHUB_REPOSITORY"],
        os.environ["PR_NUMBER"],
        os.environ["HEAD_SHA"],
    )
    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        output.write(f"published={str(published).lower()}\n")
