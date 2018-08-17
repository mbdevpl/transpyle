

def replace_line(code: str, line: int, replacement: str = '') -> str:
    return replace_scope(code, line, line, replacement)


def replace_scope(code: str, line_begin: int, line_end: int, replacement: str = '') -> str:
    assert isinstance(code, str)
    assert line_begin <= line_end
    assert isinstance(replacement, str)

    lines = code.splitlines(keepends=True)
    assert len(lines) >= line_end
    replacement_lines = replacement.splitlines(keepends=True)

    output_lines = lines[:line_begin - 1] + replacement_lines + lines[line_end:]
    output = ''.join(output_lines)
    return output


# replace_scope('a\nb\nc\nd\n', 1, 2, 'b\na\n')
