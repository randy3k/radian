# Rice: 🍚 A 21 century R console

Rice has a handful of features allow R programming faster.

Note: _Rice_ is still being developed, users should use it at their own risks. 

<img width="500px" src="https://user-images.githubusercontent.com/1690993/29305813-9e7d3eaa-8168-11e7-98b1-de0bae83c590.png"></img>


### Roadmap

- [x] lightwight, no compilation is required
- [x] multiline editing
- [x] input highlight
- [ ] output highlight
- [x] auto completion
- [ ] allow custom color scheme
- [x] mac and linux
- [x] windows
- [x] python 3
- [x] python 2
- [x] brackted paste mode
- [ ] object viewer


### Installation

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

### Troubleshooting

If _Rice_ cannot locate the R installation files automatically. You can either expose the R binary to the system `PATH` variable or export the environment variable `R_HOME`. For example,

```sh
$ export R_HOME=/usr/local/lib/R
$ rice
```

### Caveat

_Rice_ is written in pure python and built on the [prompt-toolkit](https://github.com/jonathanslenders/python-prompt-toolkit) and _Rice_ has a minimal dependency of `six`, `wcwidth`, `prompt-toolkit`, `pygments`.
