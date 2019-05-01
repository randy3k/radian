# v0.4.0

  - update rchitect to v0.3.0

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