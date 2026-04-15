"""Test environment bootstrap."""

from __future__ import annotations

import os


os.environ.setdefault("SECRET_KEY", "test-secret-key-for-suite")
os.environ.setdefault("BOOTSTRAP_ADMIN_USERNAME", "admin")
os.environ.setdefault("BOOTSTRAP_ADMIN_PASSWORD", "admin")
os.environ.setdefault("BOOTSTRAP_API_KEY", "dev-api-key-change-in-production")
