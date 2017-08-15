from setuptools import setup

try:
    import pypandoc
    long_description = pypandoc.convert_file('README.md', 'rst')
except (IOError, ImportError):
    long_description = ''


setup(
    name='rice',
    author='Randy Lai',
    version='0.0.1',
    url='https://github.com/randy3k/rice',
    description='R REPL build on top of prompt_toolkit',
    long_description=long_description,
    packages=["rice"],
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
