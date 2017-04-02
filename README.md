# Role: A 21 century R console

Role is a modern **R** cons**ole** with a handful of features allow R programming faster.

Note: _Role_ is still under development, users should use it at their own risks. Do **not** run important data on _Role_.

<img width="500px" src="https://cloud.githubusercontent.com/assets/1690993/24591455/773e3478-17cf-11e7-8cac-a76ae03d4cf5.png"></img>


### Features

Already implemented features:

- [x] multiline editing
- [x] brackted paste mode
- [x] syntax highlight
- [x] auto completion
- [x] lightwight, no compilation is required
- [x] cross-platform, work on Windows, macOS and Linux
- [x] robust, run on both Python 2 and 3

Planning features:

- [ ] function call tips
- [ ] object viewer

### Installation

```python
# install released version
pip install role
# or the development version
pip install git+https://github.com/randy3k/role
```

### Caveat

_Role_ is written in pure python and built on the [prompt-toolkit](https://github.com/jonathanslenders/python-prompt-toolkit) and _Role_ has a minimal dependency of `six`, `wcwidth`, `prompt-toolkit`, `pygments`.