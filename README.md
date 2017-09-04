# Rice: 🍚 A 21 century R console

_Rice_ is a modern command line interface to the R program. It is a pure frontend so that an R installation is required.
It replaces the use of the the default R console, similar to `ipython` in the `python` ecosystem. In fact, `rice` is built on top of the same technology which `ipython` uses. 

_Rice_ is still under active development, any feedbacks will be welcome. Users should also use it at their own risks 

<img width="500px" src="https://user-images.githubusercontent.com/1690993/29305813-9e7d3eaa-8168-11e7-98b1-de0bae83c590.png"></img>


## Features

- [x] lightwight, no compilation is required
- [x] multiline editing
- [x] syntax highlight
- [x] auto completion
- [x] brackated paste mode
- [x] cross platform, runs on Windows, macOS and Linux
- [x] run on both python 2 and 3
- [ ] vi editing mode
- [ ] more completions
- [ ] custom color scheme
- [ ] object viewer


## Installation

Requirements:

- The installation of R is required to use _Rice_, R installation binary can be downloaded from https://cran.r-project.org.
- `python` is also required to install _Rice_. If your system doesn't come with a python distribution, it can be downloaded from https://conda.io/miniconda.html. Both version 2 and version 3 should work.
- `pip` is optional but it makes the installation a bit easier.

```sh
# install released version
pip install rice
# or the development version
pip install git+https://github.com/randy3k/rice
```

## FAQ

### R_HOME location

If _Rice_ cannot locate the R installation files automatically. You can either expose the R binary to the system `PATH` variable or export the environment variable `R_HOME`. For example,

```sh
$ export R_HOME=/usr/local/lib/R
$ rice
```

If the above doesn't work, you may need to futher specify `LD_LIBRARY_PATH`,

```sh
$ export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:`R RHOME`/lib"
$ rice
```

### Does it slow down my R program?

_Rice_ only provides a frontend to the R program, the actual running engine is identical to the traditional R console. There is no performance sacrifice while enjoying the benefits of this modern command line interface. 

### Does it support Nvim-R?

Just put
```vim
let g:R_app = "rice"
let g:R_cmd = "R"
let g:R_hl_term = 0
```
in your vim config.