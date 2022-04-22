import os
import re
import sys
from setuptools import setup, find_packages


def get_long_description():
    with open('README.md', 'rb') as f:
        desc = f.read().decode('utf-8')

    return desc


def get_version(package):
    """
    Return package version as listed in `__version__` in `__init__.py`.
    """
    path = os.path.join(os.path.dirname(__file__), package, '__init__.py')
    with open(path, 'rb') as f:
        init_py = f.read().decode('utf-8')
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


tests_deps = [
    "coverage",
    "pytest",
    "pyte>=0.8.0",
    "pexpect",
    "pywinpty==0.5.7" if sys.platform.startswith("win") else "ptyprocess"
]


setup(
    name='radian',
    author='Randy Lai',
    version=get_version("radian"),
    url='https://github.com/randy3k/radian',
    description='A 21 century R console',
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    packages=find_packages('.', exclude=["tests"]),
    package_data={'radian': ['reticulate/*.R']},
    python_requires='>=3.6',
    install_requires=[
        # 'rchitect@git+https://github.com/randy3k/rchitect',
        'rchitect>=0.3.36,<0.4.0',
        'prompt_toolkit>=3.0.15,<3.1',
        'pygments>=2.5.0'
    ],
    entry_points={
        'console_scripts': [
            'radian = radian:main'
        ]
    },
    extras_require={
        "test": tests_deps
    },
    setup_requires=["pytest-runner"],
    tests_require=tests_deps
)
