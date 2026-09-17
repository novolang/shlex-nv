# Changelog

All notable changes to shlex-nv are recorded here. The format is
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
package follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
with the pre-1.0 rule that a breaking change bumps the MINOR number.

## [0.0.1] — 2026-09-17

**The interface, published before anyone implements it.** Every public
type and function carries its full signature, its effect row and its
doc comment; every body is `todo()`; the release is recorded
`implemented = false`.

### Added

- `shlexsplit` — a line into words by POSIX.1-2017 section 2.2, and
  nothing else. Splitting stops where expansion begins, because every
  expansion reads the environment, a process or a directory and this
  package reads nothing. `would_expand` is how a caller finds out that
  a word it holds would mean more to a shell than it means here.
  `words` carries offsets and a quoted flag, which is what an editor
  and a diagnostic need.
- `shlexquote` — single quotes, always, with an inner quote written
  `'\''`. Inside a single-quoted string section 2.2.2 gives no
  character a special meaning, so there is no list of metacharacters to
  maintain against every shell in existence. `is_option_like` says the
  thing quoting cannot fix: a perfectly quoted `-rf` is still `-rf` to
  the program receiving it.
- `shlexbash` — the six bash constructs that split a line into
  different words from the POSIX rules, each with the disagreement
  named. They are refused rather than split, because either answer
  would be a guess and the program would run a command nobody wrote.
- `shlexerror` — five faults, with `is_incomplete` separating a line
  that would be finished by reading more from one that would not. A
  terminal continues on the first and stops on the second, and
  `waiting_for` is what goes in its secondary prompt.

### Known

- `novo test` is red, and that is the release's expected state: every
  assertion in the API suite reaches `not implemented:
  shlex-nv.<module>.<fn>`.
- No dependencies. Section 2.2 defines quoting over four ASCII
  characters and section 2.3 delimits words on space, tab and newline,
  so every other byte is carried through untouched and a UTF-8
  argument survives without anything here knowing what UTF-8 is.
