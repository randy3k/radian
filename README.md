# rice: 🍚 A 21 century R console

_rice_ is a modern command line interface to the R program. It replaces the use of the the default R console, in the sense which is similar to `ipython` in the `python` ecosystem. In fact, `rice` is built on top of the same technology which `ipython` uses. 

_rice_ is still under active development, any feedbacks will be welcome. Users should also use it at their own risks 

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

- An installation of R (version 3.4.0 or above) is required to use _rice_, an R installation binary for your system can be downloaded from https://cran.r-project.org.
- `python` is also required to install _rice_. If your system doesn't come with a python distribution, it can be downloaded from https://conda.io/miniconda.html. Both version 2 and version 3 should work, though python 3 is recommended.
- `pip` is optional but it makes the installation a bit easier.

```sh
# install released version
pip install -U rice
# or the development version
pip install -U git+https://github.com/randy3k/rice
# to run rice
rice
```

## Settings

_rice_ can be customized via `options` in `.Rprofile` file. This file is usually located in your user home directory.

```r
options(
    rice.color_scheme = "native",
    rice.editing_mode = "emacs",
    rice.auto_match = FALSE,
    rice.auto_indentation = TRUE,
    rice.tab_size = 4,
    rice.complete_while_typing = TRUE,
    rice.auto_width = TRUE,
    rice.insert_new_line = TRUE,
    rice.history_search_no_duplicates = FALSE,
    rice.prompt = "\033[0;34mr$>\033[0m ",
    rice.shell_prompt = "\033[0;31m#!>\033[0m ",
    rice.browse_prompt = "\033[0;33mBrowse[{}]>\033[0m ",
    rice.suppress_reticulate_message = FALSE
)
```

- color scheme: see [here](https://help.farbox.com/pygments.html) for a list of supported color schemes, default is `"native"`
- editing mode: either  `"emacs"` (default) or `"vi"`.

## Alias on unix system

You could alias `r` to `rice` by putting

```bash
alias r="rice"
```
in `~/.bash_profile` such that `r` would open `rice` and `R` would still open the tranditional R console.
(`R` is still useful, e.g, running `R CMD BUILD`.)

## FAQ

### R_HOME location

If _rice_ cannot locate the R installation files automatically. You can either expose the R binary to the system `PATH` variable or export the environment variable `R_HOME`. For example,

```sh
$ export R_HOME=/usr/local/lib/R
$ rice
```
Note that it should be the path to `R_HOME`, not the path to the R binary. The folder should contain a file called `COPYING`.

If the above doesn't work, you may need to futher specify `LD_LIBRARY_PATH`,

```sh
$ export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:`R RHOME`/lib"
$ rice
```

### History file

_rice_ maintains its own history file `.rice_history` and doesn't use the `.Rhistory` file. A local `.rice_history` is used if it is found in the launching directory. Otherwise, the global history file `~/.rice_history` would be used. To override the default behavior, you could launch `rice` with the options: `rice --local-history`, `rice --global-history` or `rice --no-history`.


### Does it slow down my R program?

_rice_ only provides a frontend to the R program, the actual running eventloop is the same as that of the traditional R console. There is no performance sacrifice (or gain) while using this modern command line interface. 

### Nvim-R support

Put
```vim
let R_app = "rice"
let R_cmd = "R"
let R_hl_term = 0
let R_args = []  " if you had set any
let R_bracketed_paste = 1
```
in your vim config. 

Requires https://github.com/jalvesaq/Nvim-R/pull/258 to work seamlessly, otherwise auto indentation and auto bracket match will behave strangely.

### Package `reticulate` not working

You need to make sure that you are using the latest `reticulate`. The current developing version can be install via

```r
devtools::install_github("rstudio/reticulate")
```


### Readline Error

```
libreadline.so.6: undefined symbol: PC
```

If you are using conda and encounter this error, it is likely because the `readline` from conda is bugged. Install it again via `conda-forge`.
```python
conda install -c conda-forge readline=6.2
```
