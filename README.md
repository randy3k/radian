# Role: A 21 century R console

Role is a modern **R** cons**ole** with a handful of features allow R programming faster.

Note: _Role_ is still under development, users should use it at their own risks. Do **not** run important data on _Role_.


### Features

- [x] lightwight, no compilation is required.
- [x] brackted paste mode
- [x] multiline editing
- [x] auto completion
- [x] running on both Python 2 and 3.
- [ ] syntax color

### Installation

```python
pip install git+https://github.com/randy3k/role
```

### Caveat

_Role_ is written in pure python and built on the [prompt-toolkit](https://github.com/jonathanslenders/python-prompt-toolkit) and _Role_ has a minimal dependency of `six`, `wcwidth`, `prompt-toolkit`, `pygments`.