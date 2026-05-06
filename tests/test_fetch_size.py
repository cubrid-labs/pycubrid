"""Tests for per-cursor fetch_size property."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pycubrid.cursor import Cursor
from pycubrid.exceptions import ProgrammingError


def _make_connection(fetch_size: int = 100) -> MagicMock:
    conn = MagicMock()
    conn._fetch_size = fetch_size
    conn._timing = None
    conn._cursors = set()
    conn._decode_collections = False
    conn._json_deserializer = None
    conn._no_backslash_escapes = False
    conn._connected = True
    return conn


def test_fetch_size_default():
    """fetch_size defaults to connection-level value."""
    conn = _make_connection(fetch_size=200)
    cur = Cursor(conn)
    assert cur.fetch_size == 200


def test_fetch_size_settable():
    """fetch_size can be overridden per-cursor."""
    conn = _make_connection()
    cur = Cursor(conn)
    cur.fetch_size = 500
    assert cur.fetch_size == 500


def test_fetch_size_zero_raises():
    """fetch_size < 1 raises ProgrammingError."""
    conn = _make_connection()
    cur = Cursor(conn)
    with pytest.raises(ProgrammingError, match="fetch_size must be greater than zero"):
        cur.fetch_size = 0


def test_fetch_size_negative_raises():
    """Negative fetch_size raises ProgrammingError."""
    conn = _make_connection()
    cur = Cursor(conn)
    with pytest.raises(ProgrammingError, match="fetch_size must be greater than zero"):
        cur.fetch_size = -1
