#!/usr/bin/env python3
"""Write tests/differential_tests.nv from Python's `shlex` module.

Python's `shlex.split` in POSIX mode, with comments off, splits a line
by the same rules as `shlexsplit.split` over the characters generated
here.  The two differ on characters this generator leaves out:

- `$` and the backtick.  Inside double quotes a backslash escapes them
  under POSIX section 2.2.3, and Python keeps the backslash.
- A newline.  A backslash before one is a line continuation under
  section 2.2.1, and Python keeps the newline.  Python also treats a
  carriage return as a blank.
- `(`, `{`, `[` and `<`, which begin the bash-only forms this package
  refuses and Python splits.

For each seeded line the file records Python's words, or that Python
refused the line.  For each seeded word it records the quoted form,
which is Python's `shlex.quote` with an inner single quote written
`'\\''` rather than `'"'"'`, and checks here that Python splits it back
into the word.

Run from the package root:  python3 tools/differential.py
The output is passed through `novo fmt`.
"""
import random
import shlex
import subprocess

SEED = 20260927
ALPHABET = ['a', 'b', 'c', 'x', '1', ' ', ' ', '\t', "'", "'", '"', '"',
            '\\', '\\', '*', '?', '~', '#', '-', '=', '/', '.', ',', '@',
            '%', ';', '&', '|', '!', 'é', '→']


def nv(s):
    out = []
    for ch in s:
        if ch == '\\':
            out.append('\\\\')
        elif ch == '"':
            out.append('\\"')
        elif ch == '$':
            out.append('\\$')
        elif ch == '\t':
            out.append('\\t')
        elif ch == '\n':
            out.append('\\n')
        else:
            out.append(ch)
    return '"' + ''.join(out) + '"'


def nv_list(words):
    return '[' + ', '.join(nv(w) for w in words) + ']'


def our_quote(word):
    """Python's quote, with an inner single quote written `'\\''`."""
    if shlex.quote(word) == word:
        return word
    return "'" + word.replace("'", "'\\''") + "'"


def main():
    rng = random.Random(SEED)
    split_ok, split_refused = [], []
    while len(split_ok) < 160 or len(split_refused) < 40:
        line = ''.join(rng.choice(ALPHABET) for _ in range(rng.randint(0, 14)))
        try:
            words = shlex.split(line, comments=False, posix=True)
        except ValueError:
            if len(split_refused) < 40:
                split_refused.append(line)
            continue
        if len(split_ok) < 160:
            split_ok.append((line, words))

    words = []
    while len(words) < 80:
        w = ''.join(rng.choice(ALPHABET + ['$', '`', '(', '{', '\n'])
                    for _ in range(rng.randint(0, 8)))
        quoted = our_quote(w)
        assert shlex.split(quoted) == [w], repr((w, quoted))
        words.append((w, quoted))

    joins = []
    while len(joins) < 20:
        argv = [words[rng.randrange(len(words))][0] for _ in range(rng.randint(0, 5))]
        line = ' '.join(our_quote(w) for w in argv)
        assert shlex.split(line) == argv
        joins.append(argv)

    out = []
    out.append('''// differential_tests.nv — this package against Python's `shlex`
// module, which splits and quotes by the same rules independently.
//
// Written by tools/differential.py from seed %d; do not edit by hand.
// The lines are drawn from characters on which the two agree: no `$`,
// no backtick, no newline, and none of the characters that begin a
// bash-only form.  The script's header says why each is left out.

use std.test
use shlexsplit
use shlexquote
use shlexerror
''' % SEED)
    out.append("// Each line, and the words Python's `shlex.split` answers for it.")
    out.append('fn lines() -> [(Str, [Str])]')
    out.append('    [')
    for line, ws in split_ok:
        out.append('        (%s, %s),' % (nv(line), nv_list(ws)))
    out.append('    ]\n')
    out.append('// Lines Python refuses: each ends inside a quote or after a backslash.')
    out.append('fn refused() -> [Str]')
    out.append('    [')
    for line in split_refused:
        out.append('        %s,' % nv(line))
    out.append('    ]\n')
    out.append("// Each word, and its quoted form: Python's `shlex.quote`, with an")
    out.append("// inner single quote written `'\\\\''`.")
    out.append('fn quoted() -> [(Str, Str)]')
    out.append('    [')
    for w, q in words:
        out.append('        (%s, %s),' % (nv(w), nv(q)))
    out.append('    ]\n')
    out.append('// Lists of words that Python splits back out of their joined form.')
    out.append('fn argvs() -> [[Str]]')
    out.append('    [')
    for argv in joins:
        out.append('        %s,' % nv_list(argv))
    out.append('    ]\n')
    out.append('''@test
fn test_every_line_splits_into_the_words_python_answers() [io]
    for (line, words) in lines()
        test.case(line)
        match shlexsplit.split(line)
            Ok(argv)   => test.assert(argv == words)
            Err(fault) => test.fail(fault.message())

@test
fn test_every_line_python_refuses_is_refused_as_unfinished() [io]
    for line in refused()
        test.case(line)
        test.assert(not shlexsplit.is_complete(line))
        match shlexsplit.split(line)
            Ok(_)      => test.fail("python refuses this line")
            Err(fault) => test.assert(shlexerror.is_incomplete(fault))

@test
fn test_every_word_quotes_as_python_does_and_splits_back() [io]
    for (word, expected) in quoted()
        test.case(word)
        match shlexquote.quote(word)
            Ok(got)    =>
                test.assert(got == expected)
                match shlexsplit.split(got)
                    Ok(argv)   => test.assert(argv == [word])
                    Err(fault) => test.fail(fault.message())
            Err(fault) => test.fail(fault.message())

@test
fn test_every_joined_list_splits_back_into_itself() [io]
    for argv in argvs()
        match shlexquote.join(argv)
            Ok(line)   =>
                test.case(line)
                match shlexsplit.split(line)
                    Ok(back)   => test.assert(back == argv)
                    Err(fault) => test.fail(fault.message())
            Err(fault) => test.fail(fault.message())
''')
    path = 'tests/differential_tests.nv'
    open(path, 'w').write('\n'.join(out))
    subprocess.run(['novo', 'fmt', path], check=False)


if __name__ == '__main__':
    main()
