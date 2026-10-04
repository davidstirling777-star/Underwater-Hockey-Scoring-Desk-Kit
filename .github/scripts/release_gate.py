"""Only publish a multi-platform release if it is the newest eligible build.

Windows and Raspberry Pi 5 builds may run concurrently, but publication is
serialized. GitHub Actions does not guarantee that queued jobs run in version
order, so this check must occur inside the serialized release job.
"""
import itertools
import json
import os
import re
from urllib.request import Request, urlopen


RELEASE_TAG = re.compile(r"v(\d+)\.(\d+)\.(\d+)\Z")


def parse_version(tag):
    """Only compare this repository's three-component numeric release tags."""
    match = RELEASE_TAG.fullmatch(str(tag))
    return tuple(map(int, match.groups())) if match else None


def release_is_current(build_sha, main_sha, build_tag, releases):
    """Return (eligible, reason), independent of GitHub APIs for unit tests."""
    if build_sha != main_sha:
        return False, "a newer commit is already on main"

    version = parse_version(build_tag)
    if version is None:
        return False, "invalid release version"

    for release in releases:
        if release.get("draft") or release.get("prerelease"):
            continue
        published_version = parse_version(release.get("tag_name"))
        # A deliberate UI-series rollback may coexist briefly with a newer
        # major/minor release while the replacement build is being published.
        # Prevent stale releases only within the target major/minor series.
        if (
            published_version is not None
            and published_version[:2] == version[:2]
            and published_version >= version
        ):
            return (
                False,
                f"release {release['tag_name']} has already been published",
            )
    return True, f"{build_tag} is the newest eligible published version"


def github_get(path, token):
    """Read the GitHub API with only the workflow's short-lived token."""
    request = Request(
        f"https://api.github.com/{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "UWH-release-gate",
        },
    )
    with urlopen(request, timeout=20) as response:
        return json.load(response)


def published_releases(repository, token):
    """Inspect all published versions, rather than assuming arrival order."""
    for page in itertools.count(1):
        batch = github_get(
            f"repos/{repository}/releases?per_page=100&page={page}", token
        )
        if not isinstance(batch, list):
            raise ValueError("Unexpected GitHub releases API response")
        yield from batch
        if len(batch) < 100:
            break


def main():
    repository = os.environ["GITHUB_REPOSITORY"]
    build_sha = os.environ["GITHUB_SHA"]
    release_version = os.environ["RELEASE_VERSION"]
    token = os.environ["GITHUB_TOKEN"]
    version = f"v{release_version}"

    # Do not call the release API for builds already known to be outdated.
    main_sha = github_get(f"repos/{repository}/commits/main", token)["sha"]
    eligible, reason = release_is_current(
        build_sha, main_sha, version, []
    )
    if eligible:
        eligible, reason = release_is_current(
            build_sha, main_sha, version,
            published_releases(repository, token),
        )

    print(f"Release gate: {'publish' if eligible else 'skip'}: {reason}")
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write(f"publish={'true' if eligible else 'false'}\n")


if __name__ == "__main__":
    main()
