from setuptools import setup
import os

long_description = open(
    os.path.join(
        os.path.dirname(__file__),
        'README.md'
    )
).read()

setup(
    name='role',
    author='Randy Lai',
    version='0.0.1',
    url='https://github.com/randy3k/role',
    description='R REPL build on top of prompt_toolkit',
    long_description=long_description,
    packages=["role"],
    install_requires=[
        'prompt_toolkit>=1.0.14,<2.0.0',
        'pygments',
    ],
    entry_points={
        'console_scripts': [
            'role = role:main'
        ]
    }
)
