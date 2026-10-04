"""Choose the next numeric patch release in one major/minor series.

The classic-UI restoration deliberately returns to the 1.2 release line.
Existing 1.3 releases are ignored when choosing the next 1.2 patch number;
the publish workflow removes those superseded 1.3 releases only after the
new 1.2 release has been created successfully.
"""

import os

from release_gate import parse_version, published_releases


def next_version(series, releases):
    major_text, minor_text = series.split(".", 1)
    target = (int(major_text), int(minor_text))
    patches = []

    for release in releases:
        if release.get("draft") or release.get("prerelease"):
            continue
        version = parse_version(release.get("tag_name"))
        if version is not None and version[:2] == target:
            patches.append(version[2])

    patch = max(patches, default=0) + 1
    return f"{target[0]}.{target[1]}.{patch}"


def main():
    repository = os.environ["GITHUB_REPOSITORY"]
    token = os.environ["GITHUB_TOKEN"]
    series = os.environ.get("RELEASE_SERIES", "1.2")
    version = next_version(
        series,
        published_releases(repository, token),
    )
    print(f"Next UWH release version: {version}")
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write(f"release_version={version}\n")


if __name__ == "__main__":
    main()
