# radian: A 21 century R console

[![Main](https://github.com/randy3k/radian/actions/workflows/main.yml/badge.svg)](https://github.com/randy3k/radian/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/randy3k/radian/branch/master/graph/badge.svg)](https://codecov.io/gh/randy3k/radian)
[![](https://img.shields.io/pypi/v/radian.svg)](https://pypi.org/project/radian/)
[![Conda version](https://img.shields.io/conda/vn/conda-forge/radian.svg)](https://anaconda.org/conda-forge/radian)
<a href="https://www.paypal.me/randy3k/5usd" title="Donate to this project using Paypal"><img src="https://img.shields.io/badge/paypal-donate-blue.svg" /></a>

<img src="radian.png"></img>

_radian_ is an alternative console for the R program with multiline editing and rich syntax highlight.
One would consider _radian_ as a [ipython](https://github.com/ipython/ipython) clone for R, though its design is more aligned to [julia](https://julialang.org).
If you are looking for a Rust-based alternative, check out [arf](https://github.com/eitsupi/arf) by @eitsupi.

<img width="600px" src="https://user-images.githubusercontent.com/1690993/30728530-b5e9eb5c-9f26-11e7-8453-73a2e880c9de.png"></img>

## Features

- Cross-platform: runs on Windows, macOS, and Linux
- Shell mode: hit `;` to enter and `<backspace>` to leave
- `reticulate` Python REPL mode: hit `~` to enter
- Improved R prompt and `reticulate` Python prompt:
  - Multiline editing
  - Syntax highlighting
  - Auto-completion (`reticulate` auto-completion uses `jedi`)
- Native Unicode / UTF-8 support (including Windows with R >= 4.2)
- LaTeX symbol completion (e.g., `\alpha` + `<tab>`)
- Auto-matching parentheses and quotes
- Bracketed paste mode
- Emacs and Vi editing modes
- Automatically adjusts to terminal width
- Reads more than 4096 bytes per line

## Installation

### Requirements

- **R (>= 4.2.0)**: Download from <https://cran.r-project.org> (built with shared library `libR.so` / `libR.dylib` / `R.dll`).
- **Python (>= 3.10)**: Download from <https://www.python.org/downloads/>.

Installing `radian` via [`pipx`](https://pipx.pypa.io/stable/installation/) or [`uv`](https://docs.astral.sh/uv/) is recommended:

```sh
# install released version via pipx (or `uv tool install radian`)
pipx install radian

# or install the development version
pipx install git+https://github.com/randy3k/radian

# launch radian
radian
```

### Unix Alias

You can alias `r` to _radian_ in `~/.bashrc` or `~/.zshrc` so that `r` launches _radian_ while `R` still opens the traditional R console (useful for commands like `R CMD build`):

```bash
alias r="radian"
```

## Settings

_radian_ can be customized via R `options()` in any of the following profile files:

- `$XDG_CONFIG_HOME/radian/profile` or `$HOME/.config/radian/profile` (Unix)
- `%USERPROFILE%/radian/profile` (Windows)
- `$HOME/.radian_profile` (Unix)
- `%USERPROFILE%/.radian_profile` (Windows)
- `.radian_profile` in the current working directory

> [!NOTE]
> Specifying `radian.*` options in `.Rprofile` also works, but is not recommended because `.Rprofile` is skipped in `--vanilla` mode and may not be loaded in project-specific `renv` / `packrat` environments.

```r
# Example ~/.radian_profile — only specify the options you want to customize
options(
    radian.color_scheme = "native",
    radian.editing_mode = "emacs"
)
```

| Option | Default | Description |
| --- | --- | --- |
| `radian.color_scheme` | `"native"` | Color scheme for syntax highlighting (see [Pygments styles](https://pygments.org/styles/)) |
| `radian.editing_mode` | `"emacs"` | Key binding mode: `"emacs"` or `"vi"` |
| `radian.emacs_bindings_in_vi_insert_mode` | `FALSE` | Enable common Emacs key bindings while in Vi insert mode |
| `radian.show_vi_mode_prompt` | `TRUE` | Show Vi mode indicator when `radian.editing_mode = "vi"` |
| `radian.vi_mode_prompt` | `"\033[34m[{}]\033[0m "` | Format string (or named list `list(ins = ..., nav = ...)`) for the Vi mode indicator |
| `radian.prompt` | `"\033[34mr$>\033[0m "` | Custom R prompt string |
| `radian.shell_prompt` | `"\033[31m#!>\033[0m "` | Custom shell mode prompt string |
| `radian.browse_prompt` | `"\033[33mBrowse[{}]>\033[0m "` | Custom debug browser prompt string |
| `radian.stderr_format` | `"\033[31m{}\033[0m"` | Format string for standard error output |
| `radian.insert_new_line` | `TRUE` | Insert a blank newline between prompts |
| `radian.indent_lines` | `TRUE` | Indent continuation lines in multiline prompt |
| `radian.auto_indentation` | `TRUE` | Auto-indent new lines and curly braces |
| `radian.tab_size` | `4` | Number of spaces per indentation level |
| `radian.auto_match` | `TRUE` | Automatically match brackets and quotes |
| `radian.highlight_matching_bracket` | `FALSE` | Highlight matching brackets around the cursor |
| `radian.auto_width` | `TRUE` | Automatically adjust R `width` option when the terminal resizes |
| `radian.complete_while_typing` | `TRUE` | Show completion menu automatically while typing |
| `radian.completion_prefix_length` | `2` | Minimum prefix length to trigger auto-completion |
| `radian.completion_timeout` | `0.15` | Timeout in seconds to cancel slow completions (`0` to disable) |
| `radian.completion_adding_spaces_around_equals` | `TRUE` | Add spaces around `=` in function argument completions |
| `radian.auto_suggest` | `FALSE` | Enable `prompt_toolkit` [auto-suggestion](https://python-prompt-toolkit.readthedocs.io/en/master/pages/asking_for_input.html#auto-suggestion) from history (experimental) |
| `radian.history_size` | `20000` | Maximum number of history entries to keep |
| `radian.global_history_file` | `"~/.radian_history"` | Path to the global history file (environment variables and `~` are expanded) |
| `radian.local_history_file` | `".radian_history"` | Filename for project-local history (used instead of global history if present in the working directory) |
| `radian.history_search_no_duplicates` | `FALSE` | Skip duplicate entries during incremental history search (`Ctrl-R` / `Ctrl-S`) |
| `radian.history_search_ignore_case` | `FALSE` | Perform case-insensitive incremental history search |
| `radian.history_ignore_browser_commands` | `TRUE` | Do not save short debug browser commands (such as `n`, `s`, `c`, `Q`) in history |
| `radian.enable_reticulate_prompt` | `TRUE` | Enable `reticulate` Python REPL mode triggered by `~` |

### Custom Key Bindings

You can define custom `Escape` (or `Alt`) and `Ctrl` shortcuts in your profile. Note that some `Ctrl` keys (`m`, `i`, `h`, `d`, `c`) are reserved by the terminal and cannot be remapped.

```r
# Example: `Esc` + `-` (or `Alt` + `-` if Alt sends Escape) inserts ` <- `,
# and `Ctrl` + `Right` inserts ` %>% `
options(
    radian.escape_key_map = list(
        list(key = "-", value = " <- ")
    ),
    radian.ctrl_key_map = list(
        list(key = "right", value = " %>% ")
    )
)
```

## FAQ

#### How do I switch to a different R version or specify the R binary?

You can select which R installation _radian_ uses in several ways:

- Pass `--r-binary`: `radian --r-binary=/path/to/R`
- Expose the desired `R` binary first on `PATH`
- Set `R_BINARY=/path/to/R`
- Set `R_HOME` to the output of `R.home()` (for example, `env R_HOME=/usr/local/lib/R radian`)

#### Why can't I switch the Python runtime in `reticulate`?

_radian_ itself runs inside a Python process, so `reticulate` is bound to the Python runtime hosting _radian_ (`NOTE: Python version was forced by the current process`). To use _radian_ with a different Python environment, install _radian_ in that environment.

#### How do I enable `reticulate` auto-completions?

Install `jedi` in the same Python environment as _radian_ (e.g., `pipx inject radian jedi` or `pip install jedi`).

#### Cannot find R shared library (`libR.so` / `libR.dylib` / `R.dll`)

Make sure R was compiled with the shared library enabled. When building R from source on Linux, pass `./configure --enable-R-shlib` (and run `make clean` before rebuilding if previously compiled without it).

#### How do I use a local history file?

_radian_ stores history in `.radian_history` (separate from `.Rhistory`). If a `.radian_history` file exists in the working directory, _radian_ uses it automatically; otherwise it uses `~/.radian_history`. You can override this with `radian --local-history`, `radian --global-history`, or `radian --no-history`.

#### Does _radian_ slow down R code?

_radian_ only provides the interactive console frontend; R's evaluation loop is identical to the standard R console. However, fork-based parallelism (`parallel::mclapply` or `future::plan("multicore")`) is not recommended from an embedded R/Python process; prefer socket/multisession workers (`future::plan("multisession")`).

#### Nvim-R configuration

Add the following to your Vim/Neovim configuration:

```vim
let R_app = "radian"
let R_cmd = "R"
let R_hl_term = 0
let R_args = []  " if you had set any
let R_bracketed_paste = 1
```

#### Prompt not shown inside a Docker container

This can happen when the container's PTY size is uninitialized. Run `stty size` to check, or pass `$COLUMNS` and `$LINES` when attaching:

```sh
docker exec -it <container> bash -c "stty cols $COLUMNS rows $LINES && bash"
```

## Why called _radian_?

_radian_ is powered by (π)thon.

## Credits

_radian_ wouldn't be possible without the creative work [prompt_toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit/) by Jonathan Slenders.

