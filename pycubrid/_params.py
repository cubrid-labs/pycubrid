"""Shared parameter binding helpers used by both sync and async cursors."""

from __future__ import annotations

import datetime
import math
from decimal import Decimal
from typing import Any, Sequence

from .cursor import _split_on_placeholders
from .exceptions import ProgrammingError


def bind_parameters(
    operation: str,
    parameters: Sequence[Any],
    *,
    no_backslash_escapes: bool = False,
) -> str:
    """Substitute ? placeholders with formatted parameter literals."""
    if isinstance(parameters, Sequence) and not isinstance(parameters, (str, bytes, bytearray)):
        values = list(parameters)
    else:
        raise ProgrammingError("parameters must be a sequence")

    parts = _split_on_placeholders(operation)
    placeholder_count = len(parts) - 1
    if placeholder_count != len(values):
        raise ProgrammingError("wrong number of parameters")

    result = [parts[0]]
    for index, value in enumerate(values, start=1):
        result.append(format_parameter(value, no_backslash_escapes=no_backslash_escapes))
        result.append(parts[index])
    return "".join(result)


def format_parameter(value: Any, *, no_backslash_escapes: bool = False) -> str:
    """Convert a Python value to a SQL literal string."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, str):
        return escape_string(value, no_backslash_escapes=no_backslash_escapes)
    if isinstance(value, (bytes, bytearray)):
        return "X'%s'" % value.hex()
    if isinstance(value, datetime.datetime):
        milliseconds = value.microsecond // 1000
        if value.tzinfo is not None and value.utcoffset() is not None:
            tz_key = getattr(value.tzinfo, "key", None)
            if tz_key:
                tz_str = tz_key
            else:
                offset = value.utcoffset()
                assert offset is not None
                total_seconds = int(offset.total_seconds())
                sign = "+" if total_seconds >= 0 else "-"
                hours, remainder = divmod(abs(total_seconds), 3600)
                minutes = remainder // 60
                tz_str = "%s%02d:%02d" % (sign, hours, minutes)
            return "DATETIMETZ'%s.%03d %s'" % (
                value.strftime("%Y-%m-%d %H:%M:%S"),
                milliseconds,
                tz_str,
            )
        return "DATETIME'%s.%03d'" % (value.strftime("%Y-%m-%d %H:%M:%S"), milliseconds)
    if isinstance(value, datetime.date):
        return "DATE'%s'" % value.strftime("%Y-%m-%d")
    if isinstance(value, datetime.time):
        return "TIME'%s'" % value.strftime("%H:%M:%S")
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (int, float)):
        if math.isnan(value) or math.isinf(value):
            raise ProgrammingError("nan and inf are not supported by CUBRID")
        return str(value)
    raise ProgrammingError("unsupported parameter type")


def escape_string(value: str, *, no_backslash_escapes: bool = False) -> str:
    """Escape a string value for safe SQL embedding."""
    if "\x00" in value:
        raise ProgrammingError("string parameter contains null byte")
    if no_backslash_escapes:
        return "'%s'" % value.replace("'", "''")
    escaped = value.replace("\\", "\\\\").replace("'", "''")
    for ch in ("\r", "\n", "\x1a"):
        if ch in escaped:
            escaped = escaped.replace(ch, "\\" + ch)
    return "'%s'" % escaped


def build_description(
    columns: list[Any],
) -> tuple[tuple[Any, ...], ...] | None:
    """Build DB-API description tuple from column metadata."""
    if not columns:
        return None
    return tuple(
        (
            column.name,
            column.column_type,
            None,
            None,
            column.precision,
            column.scale,
            column.is_nullable,
        )
        for column in columns
    )
