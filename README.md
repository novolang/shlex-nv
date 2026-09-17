# shlex-nv

A shell splits a command line into words before it does anything else,
and the rules it uses are quoting rules: a backslash, a pair of single
quotes, a pair of double quotes. They are specified in
[POSIX.1-2017, Shell Command Language, section 2.2](https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html#tag_18_02).
This package splits a line into those words, quotes a word so that a
shell reads it back unchanged, and refuses the constructs bash splits
differently.

**Status: NOT IMPLEMENTED — interface only.** Every function is
declared with its full signature, but every body is a `todo()` that
panics when called. The package is published so its design can be
reviewed and depended on before it is implemented. Version 0.1.0 will
be the first working release.

## What the rules are

A **word** is a run of characters delimited by blanks. A blank is a
space or a tab. Any number of them in a row is one delimiter, and
leading and trailing blanks produce no empty words.

Four characters change that.

| Written | Meaning, from section 2.2 |
| --- | --- |
| `\` | The next character is literal. At the end of a line the backslash and the newline both disappear, which is a line continuation |
| `'…'` | Every character up to the next `'` is literal. There is no escape inside, so a single quote cannot appear in one |
| `"…"` | Every character up to the next `"` is literal, except that a backslash still escapes `$`, a backtick, `"`, `\` and a newline |
| `#` | When it begins a word, the rest of the line is a comment |

Everything else is an ordinary character. That includes `$`, a
backtick, `~`, `*` and `?`.

Those characters are ordinary here because **splitting is not
expanding**. A shell splits a line into words and then expands them: it
substitutes parameters, runs command substitutions, turns a tilde into
a home directory and a glob into file names. Each of those reads
something — the environment, a process, a directory — and this package
performs no input or output. So `echo *.txt` is two words, the second
of which is `*.txt`.

Quoting a word is the other direction. A word that needs quoting is
wrapped in single quotes, and each single quote inside it is written
`'\''`: close the string, an escaped quote, open it again. Inside a
single-quoted string no character has a special meaning at all, so
there is no list of metacharacters to keep up to date.

**Bash** adds constructs that change how a line is split. `$'a b'` is
one word in bash and two under these rules, because POSIX has no
`$'…'` quote: the `$` is an ordinary character and `'a b'` is a
single-quoted string. `<(sort f)` is one word in bash and two here.
A splitter that applied the POSIX rules to those lines would answer,
and the answer would be a command nobody wrote. They are refused by
name.

## Install

```
novo pkg add shlex-nv
```

## Example

```novo
use shlexquote
use shlexsplit

fn main() [io]
    // A line a user typed. The quotes hold one word together.
    match shlexsplit.split("cp -r 'my files' /tmp")
        Err(fault) => println("cannot read the line")
        Ok(argv)   =>
            println("${list.len(argv)} words")     // 4 words
            println(argv[2])                       // my files

    // The other direction: a list of words into a line a shell reads
    // back as those same words.
    match shlexquote.join(["grep", "it's here", "notes.txt"])
        Err(fault) => println("cannot quote: ${fault.message()}")
        Ok(line)   => println(line)                // grep 'it'\''s here' notes.txt
```

Build and test with `novo pkg build` and `novo test`. Today `novo test`
fails on purpose: every test reaches a
`not implemented: shlex-nv.<module>.<fn>` panic. The tests are the
specification the implementation will have to satisfy.

## What the package contains

| Module | Contents |
| --- | --- |
| `shlexsplit` | A line into words, with their offsets and whether each was quoted, and the questions a terminal asks about an unfinished line. |
| `shlexquote` | A word a shell reads back unchanged, a whole command line, and the thing quoting does not protect against. |
| `shlexbash` | The six bash constructs that change word splitting, each named with what the two readings disagree about. |
| `shlexerror` | Why a line was refused, and whether reading more of it would help. |

## How to choose an entry point

**`shlexsplit.split` answers a list of words.** It is what a caller
wants when the words are the point — running a command, matching a
history entry.

**`shlexsplit.words` answers the same words with their offsets and
whether each was quoted.** An editor, a syntax highlighter and a
diagnostic that points at a character all need those.

**`shlexsplit.is_complete` asks whether a line is finished.** A
terminal calls it to decide whether to print a secondary prompt.

**`shlexquote.quote` quotes one word.** `shlexquote.join` quotes a
whole list and joins it with single spaces.

**`shlexquote.quote_into` appends to a buffer the caller owns.** Use it
when a long command line is being assembled.

## The rules a user needs

1. **Nothing is expanded.** `$HOME` splits into the word `$HOME`, not
   into a directory. `*.txt` splits into the word `*.txt`, not into
   file names. `shlexsplit.would_expand` says whether a word would mean
   more to a shell than it means here.
2. **A single-quoted string has no escapes.** A backslash inside one is
   a backslash, and a single quote cannot appear at all. Section 2.2.2.
3. **A double-quoted string keeps four escapes.** A backslash retains
   its meaning only before `$`, a backtick, `"`, `\` and a newline;
   before anything else it is a backslash. Section 2.2.3.
4. **A backslash at the end of a line is a line continuation**, and
   both characters disappear. Section 2.2.1.
5. **Quotes join to the word around them.** `a'b c'd` is the single
   word `ab cd`.
6. **`#` starts a comment only when it begins a word, and only when
   asked.** `shlexsplit.options()` has comments off, because a command
   line typed at a prompt has none and a `#` in it is usually a
   character in a file name. A configuration file holding command lines
   turns them on with `shlexsplit.with_comments`.
7. **Six bash constructs are refused by name**: `$'…'`, `$"…"`,
   `<(…)` and `>(…)`, `{a,b}`, `[[ … ]]` and `(( … ))`, and the
   extended globs `?(…)` `*(…)` `+(…)` `@(…)` `!(…)`. Each of them
   splits into different words under bash and under POSIX, so
   answering either reading would be a guess. `shlexbash.first_form`
   finds the first one and where it starts.
8. **An unfinished line is not a refused line.**
   `shlexerror.is_incomplete` is true for an unclosed quote and a
   dangling backslash, and false for a bash-only form and a NUL byte.
   A terminal reads more on the first and stops on the second.
9. **Quoting is single quotes, always.** A word that needs nothing is
   returned unchanged, so an ordinary command line stays readable. The
   empty string becomes `''`, because nothing is not a word.
10. **A NUL byte cannot be quoted.** No shell can carry one in an
    argument, and dropping it would produce a command line other than
    the one asked for. `shlexquote.quote` refuses and names the offset.
11. **Quoting makes a word; it does not make the word harmless.**
    `shlexquote.quote("-rf")` is `-rf`, and the program receiving it
    decides what a leading dash means.
    `shlexquote.is_option_like` says so, and the fix — a `./` prefix,
    or a `--` before the operands — is the caller's.
12. **`shlexsplit.split(shlexquote.join(argv))` answers `argv`.** For
    every list of words holding no NUL byte. That round trip is what
    this package is for.

## What is not included

- **Every expansion**: parameters, command substitution, arithmetic,
  tilde, globs, and the field splitting a shell does *after* an
  expansion using `IFS`. Each of them reads the environment, a process
  or a directory, and this package performs no input or output.
- **Running anything.** A caller that wants to execute the words hands
  them to a process API, which is where the effect belongs.
- **Shell operators**: `|`, `&&`, `;`, `>`, `<<`, `&>`, `|&`, `<<<`.
  They are not words, and a line holding them is a command *list*,
  which is a grammar rather than a quoting rule. A caller building a
  command line is not producing them.
- **`IFS`.** The blanks are space, tab and newline, which is the
  default value. Reading a different one means reading the
  environment.
- **A `csh` or PowerShell dialect.** Their quoting rules are different
  enough that one function could not serve both without an argument
  saying which, and a caller who got that argument wrong would get a
  silently wrong split.

## Related packages

- [cli-nv](https://novo-lang.org/packages/cli-nv) parses the words this
  package produces into flags and operands. This package ends where
  that one begins.
- [glob-nv](https://novo-lang.org/packages/glob-nv) matches the glob
  patterns this package leaves as ordinary words.
- [dirs-nv](https://novo-lang.org/packages/dirs-nv) resolves the
  directories a `~` would have expanded to, by reading the
  environment.

## Tests

```bash
novo test tests/shlexsplit_tests.nv   # the four quoting characters
novo test tests/shlexquote_tests.nv   # quoting, and the round trip
novo test tests/shlexbash_tests.nv    # the six refused forms
novo test tests/shlexerror_tests.nv   # unfinished against refused
```

The normative source is POSIX.1-2017, Shell Command Language, sections
2.2 and 2.3. The reference implementations are the Rust crate `shlex`
and Python's `shlex` module, whose `split` and `quote` this package's
two halves correspond to.

The suite asserts that each quoting form behaves as section 2.2
describes, that quotes join to the word around them, that nothing is
expanded, that a line ending inside a quote is reported as incomplete,
that each of the six bash forms is found at its own offset and refused,
and that joining a list of words and splitting the result gives the
list back.

The tests compile today and fail at run, each on the
`not implemented: shlex-nv.<module>.<fn>` panic that is its body. That
is the expected state of an interface release. They turn green one at a
time as bodies land.

## Implementation status

| Item | Implemented |
| --- | --- |
| `shlexsplit.ShlexWord`, `.ShlexOptions`, `shlexbash.ShlexBashForm`, `.ShlexBashFound`, `shlexerror.ShlexFault` | the types are declared |
| `shlexsplit.split`, `.split_with`, `.words` | no |
| `shlexsplit.options`, `.with_comments`, `.comment_at` | no |
| `shlexsplit.is_complete`, `.first_word`, `.would_expand` | no |
| `shlexquote.quote`, `.quote_into`, `.join` | no |
| `shlexquote.needs_quoting`, `.is_option_like`, `.first_nul` | no |
| `shlexbash.first_form`, `.is_bash_only` | no |
| `shlexbash.form_name`, `.form_code`, `.form_disagreement` | no |
| `shlexerror.is_incomplete`, `.offset`, `.code`, `.waiting_for`, `ShlexFault.message` | no |

## Licence

Apache-2.0. See `LICENSE`.

<!-- docs/writing-a-readme.md is the style guide for this page. -->
