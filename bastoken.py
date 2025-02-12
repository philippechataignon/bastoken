#!/usr/bin/env python3
"""Tokenizes an AppleSoft BASIC program into memory representation.

See http://www.txbobsc.com/scsc/scdocumentor/D52C.html for original source.

TODO: add tests
"""

TOKENS = {}

for i, t in enumerate([
    "END", "FOR", "NEXT", "DATA", "INPUT", "DEL", "DIM", "READ", "GR", "TEXT",
    "PR#", "IN#", "CALL", "PLOT", "HLIN", "VLIN", "HGR2", "HGR", "HCOLOR=",
    "HPLOT", "DRAW", "XDRAW", "HTAB", "HOME", "ROT=", "SCALE=", "SHLOAD",
    "TRACE", "NOTRACE", "NORMAL", "INVERSE", "FLASH", "COLOR=", "POP", "VTAB",
    "HIMEM:", "LOMEM:", "ONERR", "RESUME", "RECALL", "STORE", "SPEED=", "LET",
    "GOTO", "RUN", "IF", "RESTORE", "&", "GOSUB", "RETURN", "REM", "STOP", "ON",
    "WAIT", "LOAD", "SAVE", "DEF", "POKE", "PRINT", "CONT", "LIST", "CLEAR",
    "GET", "NEW", "TAB(", "TO", "FN", "SPC(", "THEN", "AT", "NOT", "STEP", "+",
    "-", "*", "/", "^", "AND", "OR", ">", "=", "<", "SGN", "INT", "ABS", "USR",
    "FRE", "SCRN(", "PDL", "POS", "SQR", "RND", "LOG", "EXP", "COS", "SIN",
    "TAN", "ATN", "PEEK", "LEN", "STR$", "VAL", "ASC", "CHR$", "LEFT$",
    "RIGHT$", "MID$"]):
    TOKENS[t] = 0x80 + i


def tokenize_program(lines):
    """Tokenizes a program consisting of multiple lines."""

    addr = 0x801
    for line in lines:
        # Skip lines that entirely consist of other whitespace,
        # though we want to keep this for actual program lines
        if not line.strip():
            continue
        # ignore line beginning with '#'
        if line[0] == "#":
            continue
        linenum, tokenized = tokenize_line(line.rstrip("\n\r"))
        tokenized = list(tokenized)
        addr += len(tokenized) + 4
        # Starting address of next program line (or EOF)
        yield addr & 0xff
        yield addr >> 8 & 0xff
        # Line number
        yield linenum & 0xff
        yield linenum >> 8 & 0xff
        # Statement body
        yield from tokenized
    # No more lines : three 0 at the end
    yield 0x00
    yield 0x00
    yield 0x00


def tokenize_line(line: str):
    """Tokenizes a program line consisting of line number and statement body."""

    line_num_str = ""
    for idx, char in enumerate(line):
        if char >= '0' and char <= '9':
            line_num_str += char
        else:
            break
    line_num = int(line_num_str)
    if line_num > 65535:
        raise ValueError(line_num)

    return int(line_num), tokenize_statements(line[idx:])


def tokenize_statements(line: str):
    """Emits sequence of tokens for a line statement body."""

    data_mode = False  # Are we inside a DATA statement?
    rem_mode = False  # Are we inside a REM statement?
    quote_mode = False  # Are we inside a quoted string?

    char_idx = 0
    while char_idx < len(line):
        char = line[char_idx]

        if char == " " and not (data_mode or rem_mode or quote_mode):
            char_idx += 1
            continue

        if char == '"':
            quote_mode = not quote_mode

        if char == ':':
            data_mode = False
            yield ord(char)
            char_idx += 1
            continue

        if quote_mode or rem_mode or data_mode:
            yield ord(char)
            char_idx += 1
            continue

        if char == '?':
            yield TOKENS["PRINT"]
            char_idx += 1
            continue

        if '0' <= char <= ';':
            yield ord(char)
            char_idx += 1
            continue

        tokens, char_idx = read_token(line, char_idx)
        for token in tokens:
            if token == TOKENS["DATA"]:
                data_mode = True
            elif token == TOKENS["REM"]:
                rem_mode = True
            yield token
    yield 0x00


def read_token(line: str, idx: int):
    """Reads forward from idx and emits next matching token(s)."""
    for token in TOKENS:
        lookahead_idx = idx
        token_idx = 0
        token_match = False
        while lookahead_idx < len(line) and token_idx < len(token):
            char = line[lookahead_idx]
            if char == " ":
                lookahead_idx += 1
                continue

            if char.upper() != token[token_idx]:
                break
            if token_idx == len(token) - 1:
                token_match = True
                break

            lookahead_idx += 1
            token_idx += 1
        if token_match:
            break

    if not token_match:
        # Didn't find one, next character must be a literal
        return [ord(line[idx].upper())], idx + 1

    # need to read one more char to disambiguate "AT/ATN/A TO"
    if token == "AT":
        if line[lookahead_idx + 1] == "N":
            return [TOKENS["ATN"]], lookahead_idx + 2
        elif line[lookahead_idx + 1] == "O":
            return [ord("A"), TOKENS["TO"]], lookahead_idx + 2
    return [TOKENS[token]], lookahead_idx + 1

def main():
    import sys
    if len(sys.argv) < 3 or sys.argv[2] == "-":
        outfile = sys.stdout
    else:
        outfile = open(sys.argv[2], "wb")
    if len(sys.argv) < 2 or sys.argv[1] == "-":
        infile = sys.stdin
    else:
        infile = open(sys.argv[1], "r")
    outfile.buffer.write(bytes([c for c in tokenize_program(infile)]))

if __name__ == "__main__":
    main()
