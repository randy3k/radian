# rtichoke: A 21 century R console

<img src="rtichoke.png"></img>

_rtichoke_ is an enhanced console for the R program. `rtichoke` is built on top of the python library `prompt-toolkit`. In some sense, one would consider `rtichoke` as a [ipython](https://github.com/ipython/ipython) clone for R. _rtichoke_ was previously named as _rice_.

_rtichoke_ is still under active development, any feedbacks will be welcome. Users should also use it at their own risks 

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

- An installation of R (version 3.4.0 or above) is required to use _rtichoke_, an R installation binary for your system can be downloaded from https://cran.r-project.org.
- `python` is also required to install _rtichoke_. If your system doesn't come with a python distribution, it can be downloaded from https://conda.io/miniconda.html. Both version 2 and version 3 should work, though python 3 is recommended.
- `pip` is optional but it makes the installation a bit easier.

```sh
# install released version
pip install -U rtichoke
# or the development version
pip install -U git+https://github.com/randy3k/rtichoke
# to run rtichoke
rtichoke
```

## Settings

_rtichoke_ can be customized via `options` in `.Rprofile` file. This file is usually located in your user home directory.

```r
options(
    # color scheme see [here](https://help.farbox.com/pygments.html) for a list of supported color schemes, default is `"native"`
    rtichoke.color_scheme = "native",

    # either  `"emacs"` (default) or `"vi"`.
    rtichoke.editing_mode = "emacs",

    # auto match brackets and quotes
    rtichoke.auto_match = FALSE,

    # auto indentation for new line and curly braces
    rtichoke.auto_indentation = TRUE,
    rtichoke.tab_size = 4,

    # pop up completion while typing
    rtichoke.complete_while_typing = TRUE,

    # automatically adjust R buffer size based on terminal width
    rtichoke.auto_width = TRUE,

    # insert new line between prompts
    rtichoke.insert_new_line = TRUE,

    # when using history search (ctrl-r/ctrl-s in emacs mode), do not show duplicate results
    rtichoke.history_search_no_duplicates = FALSE,

    # custom prompt for different modes
    rtichoke.prompt = "\033[0;34mr$>\033[0m ",
    rtichoke.shell_prompt = "\033[0;31m#!>\033[0m ",
    rtichoke.browse_prompt = "\033[0;33mBrowse[{}]>\033[0m ",

    # supress the loading message for reticulate
    rtichoke.suppress_reticulate_message = FALSE
)
```

## Alias on unix system

You could alias `r` to `rtichoke` by putting

```bash
alias r="rtichoke"
```
in `~/.bash_profile` such that `r` would open `rtichoke` and `R` would still open the tranditional R console.
(`R` is still useful, e.g, running `R CMD BUILD`.)

## FAQ

### R_HOME location

If _rtichoke_ cannot locate the installation of R automatically. The best option is to expose the R binary to the system `PATH` variable. 

On Linux/macOS, you could also export the environment variable `R_HOME`. For example,
```sh
$ export R_HOME=/usr/local/lib/R
$ rtichoke
```
Note that it should be the path to `R_HOME`, not the path to the R binary. The
folder should contain a file called `COPYING`. In some cases, you may need to
futher specify `LD_LIBRARY_PATH`,
```sh
$ export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:`R RHOME`/lib"
$ rtichoke
```

### History file

_rtichoke_ maintains its own history file `.rtichoke_history` and doesn't use the `.Rhistory` file. A local `.rtichoke_history` is used if it is found in the launching directory. Otherwise, the global history file `~/.rtichoke_history` would be used. To override the default behavior, you could launch `rtichoke` with the options: `rtichoke --local-history`, `rtichoke --global-history` or `rtichoke --no-history`.


### Does it slow down my R program?

_rtichoke_ only provides a frontend to the R program, the actual running eventloop is the same as that of the traditional R console. There is no performance sacrifice (or gain) while using this modern command line interface. 

### Nvim-R support

Put
```vim
let R_app = "rtichoke"
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


## Credits

`rtichoke` wouldn't be possible witout the creative work [prompt_toolkit](https://github.com/jonathanslenders/python-prompt-toolkit/) by Jonathan Slenders.

The name `rtichoke` was suggested by [thefringthing](https://www.reddit.com/r/rstats/comments/7zibhj/any_suggestions_of_a_new_name_of_rice/).

<div>Icons made by <a href="http://www.freepik.com" title="Freepik">Freepik</a> from <a href="https://www.flaticon.com/" title="Flaticon">www.flaticon.com</a> is licensed by <a href="http://creativecommons.org/licenses/by/3.0/" title="Creative Commons BY 3.0" target="_blank">CC 3.0 BY</a></div>