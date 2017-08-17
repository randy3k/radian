import os
import re
from setuptools import setup, find_packages

try:
    import pypandoc
    long_description = pypandoc.convert_file('README.md', 'rst')
except:
    long_description = ''


def get_version(package):
    """
    Return package version as listed in `__version__` in `__init__.py`.
    """
    path = os.path.join(os.path.dirname(__file__), package, '__init__.py')
    with open(path, 'rb') as f:
        init_py = f.read().decode('utf-8')
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)

setup(
    name='rice',
    author='Randy Lai',
    version=get_version("rice"),
    url='https://github.com/randy3k/rice',
    description='R CLI built on top of prompt_toolkit',
    long_description=long_description,
    packages=find_packages('.'),
    install_requires=[
        'pygments',
        'six',
        'wcwidth'
    ],
    entry_points={
        'console_scripts': [
            'rice = rice:main'
        ]
    }
)
