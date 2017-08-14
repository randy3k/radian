from setuptools import setup

try:
    import pypandoc
    long_description = pypandoc.convert_file('README.md', 'rst')
except (IOError, ImportError):
    long_description = ''


setup(
    name='role',
    author='Randy Lai',
    version='0.0.3-dev',
    url='https://github.com/randy3k/role',
    description='R REPL build on top of prompt_toolkit',
    long_description=long_description,
    packages=["role"],
    install_requires=[
        'pygments',
        'six',
        'wcwidth'
    ],
    entry_points={
        'console_scripts': [
            'role = role:main'
        ]
    }
)
