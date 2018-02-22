# rtifact: 🍚 A 21 century R console

_rtifact_ is a modern command line interface to the R program. It replaces the use of the default R console, in the sense like what `ipython` does in the `python` ecosystem. Actually, `rtifact` and `ipython` are based on the same library `prompt-toolkit`.

_rtifact_ is still under active development, any feedbacks will be welcome. Users should also use it at their own risks 

<img width="600px" src="https://user-images.githubusercontent.com/1690993/30728530-b5e9eb5c-9f26-11e7-8453-73a2e880c9de.png"></img>


## Features

- [x] shell mode (hit `;` to enter and `<backspace>` to leave)
- [x] lightweight, no compilation is required
- [x] multiline editing
- [x] syntax highlight
- [x] auto completion
- [x] auto matching parens/quotes.
- [x] brackated paste mode
- [x] cross platform, runs on Windows, macOS and Linux
- [x] emacs/vi editing mode
- [x] custom color scheme
- [x] automiatically adjust to terminal width
- [x] read more than 4096 bytes per line


## Installation

Requirements:

- An installation of R (version 3.4.0 or above) is required to use _rtifact_, an R installation binary for your system can be downloaded from https://cran.r-project.org.
- `python` is also required to install _rtifact_. If your system doesn't come with a python distribution, it can be downloaded from https://conda.io/miniconda.html. Both version 2 and version 3 should work, though python 3 is recommended.
- `pip` is optional but it makes the installation a bit easier.

```sh
# install released version
pip install -U rtifact
# or the development version
pip install -U git+https://github.com/randy3k/rtifact
# to run rtifact
rtifact
```

## Settings

_rtifact_ can be customized via `options` in `.Rprofile` file. This file is usually located in your user home directory.

```r
options(
    # color scheme see [here](https://help.farbox.com/pygments.html) for a list of supported color schemes, default is `"native"`
    rtifact.color_scheme = "native",

    # either  `"emacs"` (default) or `"vi"`.
    rtifact.editing_mode = "emacs",

    # auto match brackets and quotes
    rtifact.auto_match = FALSE,

    # auto indentation for new line and curly braces
    rtifact.auto_indentation = TRUE,
    rtifact.tab_size = 4,

    # pop up completion while typing
    rtifact.complete_while_typing = TRUE,

    # automatically adjust R buffer size based on terminal width
    rtifact.auto_width = TRUE,

    # insert new line between prompts
    rtifact.insert_new_line = TRUE,

    # when using history search (ctrl-r/ctrl-s in emacs mode), do not show duplicate results
    rtifact.history_search_no_duplicates = FALSE,

    # custom prompt for different modes
    rtifact.prompt = "\033[0;34mr$>\033[0m ",
    rtifact.shell_prompt = "\033[0;31m#!>\033[0m ",
    rtifact.browse_prompt = "\033[0;33mBrowse[{}]>\033[0m ",

    # supress the loading message for reticulate
    rtifact.suppress_reticulate_message = FALSE
)
```

## Alias on unix system

You could alias `r` to `rtifact` by putting

```bash
alias r="rtifact"
```
in `~/.bash_profile` such that `r` would open `rtifact` and `R` would still open the tranditional R console.
(`R` is still useful, e.g, running `R CMD BUILD`.)

## FAQ

### R_HOME location

If _rtifact_ cannot locate the installation of R automatically. The best option is to expose the R binary to the system `PATH` variable. 

On Linux/macOS, you could also export the environment variable `R_HOME`. For example,
```sh
$ export R_HOME=/usr/local/lib/R
$ rtifact
```
Note that it should be the path to `R_HOME`, not the path to the R binary. The
folder should contain a file called `COPYING`. In some cases, you may need to
futher specify `LD_LIBRARY_PATH`,
```sh
$ export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:`R RHOME`/lib"
$ rtifact
```

### History file

_rtifact_ maintains its own history file `.rtifact_history` and doesn't use the `.Rhistory` file. A local `.rtifact_history` is used if it is found in the launching directory. Otherwise, the global history file `~/.rtifact_history` would be used. To override the default behavior, you could launch `rtifact` with the options: `rtifact --local-history`, `rtifact --global-history` or `rtifact --no-history`.


### Does it slow down my R program?

_rtifact_ only provides a frontend to the R program, the actual running eventloop is the same as that of the traditional R console. There is no performance sacrifice (or gain) while using this modern command line interface. 

### Nvim-R support

Put
```vim
let R_app = "rtifact"
let R_cmd = "R"
let R_hl_term = 0
let R_args = []  " if you had set any
let R_bracketed_paste = 1
```
in your vim config. 


### Readline Error

```
libreadline.so.6: undefined symbol: PC
```

If you are using conda and encounter this error, it is likely because the `readline` from conda is bugged. Install it again via `conda-forge`.
```python
conda install -c conda-forge readline=6.2
```
