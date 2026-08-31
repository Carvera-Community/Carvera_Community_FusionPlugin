#!/usr/bin/env python3
"""Resolve whether a requested release must be a prerelease."""

from __future__ import annotations

import argparse

from scripts.build_release import is_prerelease


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--publish-stable-from-non-main", action="store_true")
    args = parser.parse_args()

    print(
        "true"
        if is_prerelease(
            args.version,
            args.ref,
            args.publish_stable_from_non_main,
        )
        else "false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
