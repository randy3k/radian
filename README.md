# rice: 🍚 A 21 century R console

_rice_ is a modern command line interface to the R program. It is a pure frontend so that an R installation is required.
It replaces the use of the the default R console, similar to `ipython` in the `python` ecosystem. In fact, `rice` is built on top of the same technology which `ipython` uses. 

_rice_ is still under active development, any feedbacks will be welcome. Users should also use it at their own risks 

<img width="600px" src="https://user-images.githubusercontent.com/1690993/30728530-b5e9eb5c-9f26-11e7-8453-73a2e880c9de.png"></img>


## Features

- [x] shell mode (hit `;` to enter and `<backspace>` to leave)
- [x] lightweight, no compilation is required
- [x] multiline editing
- [x] syntax highlight
- [x] auto completion
- [x] brackated paste mode
- [x] cross platform, runs on Windows, macOS and Linux
- [x] run on both python 2 and 3
- [x] vi editing mode
- [x] custom color scheme
- [x] read more than 4096 bytes per line


## Installation

Requirements:

- An installation of R is required to use _rice_, R installation binary can be downloaded from https://cran.r-project.org.
- `python` is also required to install _rice_. If your system doesn't come with a python distribution, it can be downloaded from https://conda.io/miniconda.html. Although both version 2 and version 3 should work, I recommend using python 3.
- `pip` is optional but it makes the installation a bit easier.

```sh
# install released version
pip install -U rice
# or the development version
pip install -U git+https://github.com/randy3k/rice
```

## Settings

_rice_ can be customized by executing the `options` function in `.Rprofile` file. This file is usually located in your user home directory.

```r
options(
    rice.color_scheme = "native",
    rice.editing_mode = "emacs",
    rice.auto_indentation = TRUE,
    rice.tab_size = 4,
    rice.complete_while_typing = TRUE,
    rice.prompt = "\033[0;34mr$>\033[0m ",
    rice.shell_prompt = "\033[0;31m#!>\033[0m "
)
```

- color scheme: see [here](https://help.farbox.com/pygments.html) for a list of supported color schemes, default is `"native"`
- editing mode: either  `"emacs"` (default) or `"vi"`.

## Alias

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

### Does it slow down my R program?

_rice_ only provides a frontend to the R program, the actual running engine is identical to the traditional R console. There is no performance sacrifice while enjoying the benefits of this modern command line interface. 

### Nvim-R support

Just put
```vim
let g:R_app = "rice"
let g:R_cmd = "R"
let g:R_hl_term = 0
```
in your vim config. You may also want to set `options(rice.auto_indentation = FALSE)` in `.Rprofile`.

### Error `libreadline.so.6: undefined symbol: PC`

If you are using conda and encounter this error, it is likely because the `readline` from conda is bugged. Install it again via `conda-forge`.
```python
conda install -c conda-forge readline=6.2
```
