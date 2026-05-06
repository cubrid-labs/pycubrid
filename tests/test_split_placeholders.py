"""Tests for _split_on_placeholders() safe parameter binding."""

from __future__ import annotations

import pytest

from pycubrid.cursor import _split_on_placeholders


class TestSplitOnPlaceholders:
    """Verify ? splitting respects quotes and comments."""

    def test_simple(self):
        assert _split_on_placeholders("SELECT * FROM t WHERE id = ?") == [
            "SELECT * FROM t WHERE id = ", ""
        ]

    def test_multiple_placeholders(self):
        assert _split_on_placeholders("INSERT INTO t (a, b) VALUES (?, ?)") == [
            "INSERT INTO t (a, b) VALUES (", ", ", ")"
        ]

    def test_no_placeholders(self):
        assert _split_on_placeholders("SELECT 1") == ["SELECT 1"]

    def test_question_in_single_quoted_string(self):
        parts = _split_on_placeholders("SELECT * FROM t WHERE name = 'what?' AND id = ?")
        assert len(parts) == 2  # only 1 real placeholder
        assert "what?" in parts[0]

    def test_doubled_quote_escape(self):
        parts = _split_on_placeholders("SELECT * FROM t WHERE name = 'it''s a question?' AND id = ?")
        assert len(parts) == 2
        assert "it''s a question?" in parts[0]

    def test_question_in_double_quoted_identifier(self):
        parts = _split_on_placeholders('SELECT "col?" FROM t WHERE id = ?')
        assert len(parts) == 2
        assert 'col?' in parts[0]

    def test_question_in_line_comment(self):
        parts = _split_on_placeholders("-- why?\nSELECT * FROM t WHERE id = ?")
        assert len(parts) == 2
        assert "why?" in parts[0]

    def test_question_in_block_comment(self):
        parts = _split_on_placeholders("/* why? */ SELECT * FROM t WHERE id = ?")
        assert len(parts) == 2
        assert "why?" in parts[0]

    def test_mixed_comments_and_strings(self):
        sql = "/* hint? */ SELECT * FROM t WHERE name = 'q?' AND -- comment?\nid = ?"
        parts = _split_on_placeholders(sql)
        assert len(parts) == 2

    def test_optimizer_hint_with_question(self):
        parts = _split_on_placeholders("/*+ hint? */ SELECT * FROM t WHERE id = ?")
        assert len(parts) == 2

    def test_empty_string(self):
        assert _split_on_placeholders("") == [""]

    def test_only_placeholder(self):
        assert _split_on_placeholders("?") == ["", ""]

    def test_unterminated_string_is_lenient(self):
        # Malformed SQL - don't crash, let CUBRID reject it
        parts = _split_on_placeholders("SELECT 'unterminated")
        assert len(parts) == 1  # no placeholder found

    def test_unterminated_block_comment(self):
        parts = _split_on_placeholders("/* unterminated SELECT ? FROM t")
        assert len(parts) == 1  # ? is inside comment, no placeholder
