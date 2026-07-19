#!/usr/bin/env python3
"""Download exact Dropbox files using refresh-token authentication."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import dropbox


def dbx_client() -> dropbox.Dropbox:
    values = {
        "DROPBOX_APP_KEY": os.getenv("DROPBOX_APP_KEY"),
        "DROPBOX_APP_SECRET": os.getenv("DROPBOX_APP_SECRET"),
        "DROPBOX_REFRESH_TOKEN": os.getenv("DROPBOX_REFRESH_TOKEN"),
    }
    missing = [key for key, value in values.items() if not value]
    if missing:
        raise RuntimeError("Missing GitHub secrets: " + ", ".join(missing))
    return dropbox.Dropbox(
        oauth2_refresh_token=values["DROPBOX_REFRESH_TOKEN"],
        app_key=values["DROPBOX_APP_KEY"],
        app_secret=values["DROPBOX_APP_SECRET"],
        timeout=900,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mapping",
        nargs="+",
        help="Dropbox path and local path separated by ::",
    )
    args = parser.parse_args()
    client = dbx_client()
    client.users_get_current_account()

    for item in args.mapping:
        if "::" not in item:
            raise ValueError(f"Invalid mapping: {item}")
        remote, local = item.split("::", 1)
        destination = Path(local)
        destination.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading {remote} -> {destination}")
        client.files_download_to_file(str(destination), remote)
        if not destination.exists() or destination.stat().st_size == 0:
            raise RuntimeError(f"Downloaded file is empty: {destination}")
        print(f"Downloaded {destination.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
