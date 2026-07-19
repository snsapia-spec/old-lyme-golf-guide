#!/usr/bin/env python3
"""Download an already-extracted Dropbox shared folder recursively.

Authentication uses a Dropbox app refresh token so GitHub Actions never stores
short-lived access tokens in the repository.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path, PurePosixPath

import dropbox
from dropbox.files import FileMetadata, FolderMetadata


def client() -> dropbox.Dropbox:
    required = {
        "DROPBOX_APP_KEY": os.getenv("DROPBOX_APP_KEY"),
        "DROPBOX_APP_SECRET": os.getenv("DROPBOX_APP_SECRET"),
        "DROPBOX_REFRESH_TOKEN": os.getenv("DROPBOX_REFRESH_TOKEN"),
    }
    missing = [name for name, value in required.items() if not value]
    if missing: