# v0.5.4

  - support microsoft store python
  - reqiure rchitect 0.3.25

# v0.5.2

  - reqiure rchitect 0.3.23
  - better support of later::later with rchitect 0.3.23
  - a workaround to make "print(" completion faster

# v0.5.2

  - some code introduced in earlier to support later::later lead to
    high cpu loading, disable it for now

# v0.5.1

  - fix a bug in malformed input
  - revert: disable completion timeout in v0.5.0

# v0.5.0

 - support of R 4.0 raw strings
 - disable completion timeout

# v0.4.9

  - require rchitect 0.3.20

# v0.4.8

  - bug unicode rendering problem in python 2
  - process events in rare mode
  - better support later::later
  - require rchitect 0.3.19

# v0.4.7

 - switch from ANSICON to CMDER_ROOT to support crayon
 - added history_search_ignore_case
 - accept some common settings from plain R

# v0.4.6

 - enable crayon via ANSICON env variable instead of options crayon.enabled
 - fix a bug of nested read console when loading R.cache

# v0.4.5

 - enable crayon on windows terminals
 - allow c-x c-e to edit in editor
 - support askpass
 - add radian.highlight_matching_bracket

# v0.4.4

  - latex completion
  - require rchitect 0.3.16 for better windows support

# v0.4.3

  - add a space before and after equal sign in completion
  - requires rchitect 0.3.14 to fix a bug for R 3.6.2-dev

# v0.4.2

  - handle carriage return in stderr
  - make sure settings are in correct type

# v0.4.1

   - stderr coloring for unix
   - check if cursor is at an empty line when start a prompt
   - add vi mode state in prompt
   - support .radian_profile
   - allow -q flag
   - Added custom R lexer for better colour

# v0.4.0

  - update rchitect to version 0.3
  - add setting `radian.escape_key_map`

# v0.3.4

  - fix R_SHARE_DIR issues

# v0.3.3

  - patch reticulate

# v0.3.2

  - get R_SHARE_DIR etc from R if they don't exist

# v0.3.1

 - fix reticulate repl completion error

# v0.3.0

 - reband as radian

# v0.2.15

 - use rchitect

# v0.2.14

- fix typo completion_timeout
- .py namespace is deprecated, use .pythonapi global var

# v0.2.12

- fix backspace

# v0.2.11

- bug fix for execv on linux

# v0.2.10

- enable suspension via ctrl+z

# v0.2.9

- bump minimum requirement of rapi to v0.1.2 to fix #64

# v0.2.8

- bump minimum requirement of rapi and lineedit

# v0.2.7

- new option `indent_lines`
- improveLD_LIBRARY_PATH and R_LD_LIBRARY_PATH detection

# v0.2.4

- add backspace to exit reticulte repl mode
- do not pass `--restore-data` to R


# v0.2.3

- bump up rapi to 0.1.0


# v0.2.2

- bracketed paste check for empty data
- bump minimum requirement of linedit

# v0.2.1

- change default color scheme to "native"
- bump minimum requirement of rapi

# v0.2.0

rtichoke is undergoing a major refactoring to extract the R initialization code to [`rapi`](https://github.com/randy3k/rapi). The hope is to make rtichoke more autonomous.

Features:

- Unicode support on Windows
- reticulate mode
    - syntax highlight
    - multiline
    - autocompletion

Others:
    - change default to monokai