import json
import re
import textwrap
from typing import Any

MAX_WIDTH = 72

REMOVE_MULTI_LINES = re.compile(r"\s+")


def dedupe_list_keep_order(lst: list[Any]) -> list[Any]:
    """
    Remove duplicates from a list while preserving order.
    Uses string to handle elements like dicts that are not hashable.
    """
    seen = set()
    data = []
    for x in lst:
        if str(x) not in seen:
            data.append(x)
            seen.add(str(x))
    return data


def to_markdown(data: str | list | dict) -> str:
    """Convert a JSON string or already-parsed data (dict or list) into
    a simple Markdown representation.

    :param data: The input data, either as a JSON string, or a parsed list/dict.
    :return: A string containing the generated Markdown output.
    """
    if isinstance(data, str):
        data = json.loads(data)

    if isinstance(data, list):
        new_data = []
        for index, item in enumerate(data, start=1):
            new_data.append({f"Record {index}": item})
        data = new_data

    lines: list[str] = []
    process_any(data, [], lines)
    return ("\n".join(lines)).strip() + "\n"


def wrap_preserve_newlines(text: str, width: int) -> list[str]:
    """For each line in the text (split by newlines), wrap it to 'width' columns.
    Blank lines are preserved. Returns a list of wrapped lines without
    inserting extra blank lines.

    :param text: The multiline string to wrap.
    :param width: Maximum line width for wrapping.
    :return: A list of lines after wrapping.
    """
    wrapped_lines: list[str] = []
    for line in text.splitlines(keepends=False):
        if not line.strip():
            wrapped_lines.append("")
            continue
        # remove excessive spaces (pmid=38296628)
        line = REMOVE_MULTI_LINES.sub(" ", line)
        pieces = textwrap.wrap(line, width=width)
        wrapped_lines.extend(pieces)
    return wrapped_lines


def append_line(lines: list[str], line: str) -> None:
    """Append a line to 'lines', avoiding consecutive blank lines.

    :param lines: The running list of lines to which we add.
    :param line: The line to append.
    """
    line = line.rstrip()
    lines.append(line)


def process_any(
    value: Any,
    path_keys: list[str],
    lines: list[str],
) -> None:
    """Dispatch function to handle dict, list, or scalar (str/int/float/bool).

    :param value: The current JSON data node.
    :param path_keys: The list of keys leading to this node (for headings).
    :param lines: The running list of output Markdown lines.
    """
    if isinstance(value, dict):
        process_dict(value, path_keys, lines)
    elif isinstance(value, list):
        process_list(value, path_keys, lines)
    elif value is not None:
        render_key_value(lines, path_keys[-1], value)


def process_dict(dct: dict, path_keys: list[str], lines: list[str]) -> None:
    """Handle a dictionary by printing a heading for the current path (if any),
    then processing key/value pairs in order: scalars first, then nested dicts, then lists.

    :param dct: The dictionary to process.
    :param path_keys: The list of keys leading to this dict (for heading).
    :param lines: The running list of output Markdown lines.
    """
    if path_keys:
        level = min(len(path_keys), 5)
        heading_hash = "#" * level
        heading_text = transform_key(path_keys[-1])
        # Blank line, then heading
        append_line(lines, "")
        append_line(lines, f"{heading_hash} {heading_text}")

    # Group keys by value type
    scalar_keys = []
    dict_keys = []
    list_keys = []

    for key, val in dct.items():
        if isinstance(val, str | int | float | bool) or val is None:
            scalar_keys.append(key)
        elif isinstance(val, dict):
            dict_keys.append(key)
        elif isinstance(val, list):
            list_keys.append(key)

    # Process scalars first
    for key in scalar_keys:
        next_path = path_keys + [key]
        process_any(dct[key], next_path, lines)

    # Process dicts second
    for key in dict_keys:
        next_path = path_keys + [key]
        process_any(dct[key], next_path, lines)

    # Process lists last
    for key in list_keys:
        next_path = path_keys + [key]
        process_any(dct[key], next_path, lines)


def process_list(lst: list, path_keys: list[str], lines: list[str]) -> None:
    """If all items in the list are scalar, attempt to render them on one line
    if it fits, otherwise use bullet points. Otherwise, we recursively
    process each item.

    :param lst: The list of items to process.
    :param path_keys: The keys leading to this list.
    :param lines: The running list of Markdown lines.
    """
    all_scalars = all(isinstance(i, str | int | float | bool) for i in lst)
    lst = dedupe_list_keep_order(lst)
    if path_keys and all_scalars:
        key = path_keys[-1]
        process_scalar_list(key, lines, lst)
    else:
        for item in lst:
            process_any(item, path_keys, lines)


def process_scalar_list(key: str, lines: list[str], lst: list) -> None:
    """Print a list of scalars either on one line as "Key: item1, item2, ..."
    if it fits within MAX_WIDTH, otherwise print a bullet list.

    :param key: The key name for this list of scalars.
    :param lines: The running list of Markdown lines.
    :param lst: The actual list of scalar items.
    """
    label = transform_key(key)
    items_str = ", ".join(str(item) for item in lst)
    single_line = f"{label}: {items_str}"
    if len(single_line) <= MAX_WIDTH:
        append_line(lines, single_line)
    else:
        # bullet list
        append_line(lines, f"{label}:")
        for item in lst:
            bullet = f"- {item}"
            append_line(lines, bullet)


def render_key_value(lines: list[str], key: str, value: Any) -> None:
    """Render a single "key: value" pair. If the value is a long string,
    we do multiline wrapping with an indentation for clarity. Otherwise,
    it appears on the same line.

    :param lines: The running list of Markdown lines.
    :param key: The raw key name (untransformed).
    :param value: The value associated with this key.
    """
    label = transform_key(key)
    val_str = str(value)

    # If the value is a fairly long string, do multiline
    if isinstance(value, str) and len(value) > MAX_WIDTH:
        append_line(lines, f"{label}:")
        for wrapped in wrap_preserve_newlines(val_str, MAX_WIDTH):
            append_line(lines, "  " + wrapped)
    else:
        append_line(lines, f"{label}: {val_str}")


def transform_key(s: str) -> str:
    # Replace underscores with spaces.
    s = s.replace("_", " ")
    # Insert a space between an uppercase letter followed by an uppercase letter then a lowercase letter.
    s = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", s)
    # Insert a space between a lowercase letter or digit and an uppercase letter.
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", s)

    words = s.split()
    transformed_words = []
    for word in words:
        transformed_words.append(word.capitalize())
    return " ".join(transformed_words)
