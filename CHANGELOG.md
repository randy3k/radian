# Changelog

## 0.6.14 - 2025-05-04

### Bug Fixes

* fix: use --no-echo instread of --slave

### Miscellaneous

* chore: update changelog
* chore: update Makefile
* chore: add test section in git-changelog
* chore: update changelog for v0.6.14

### Other

* reticulate dev ([#490](https://github.com/randy3k/radian/pull/490))
* Force insert libRBlas in macOS ([#492](https://github.com/randy3k/radian/pull/492))
* change to pyproject.toml ([#516](https://github.com/randy3k/radian/pull/516))
* check if the buffer is our ModelBuffer
* revert: restore old CHANGELOG.md
* use git-cliff to gnerate changelog

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.6.13...v0.6.14

## 0.6.13 - 2024-08-15

### Bug Fixes

* fix line wrapping for windows terminal ([#484](https://github.com/randy3k/radian/pull/484))

### Other

* change R and python versions
* bump to 0.6.13

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.6.12...v0.6.13

## 0.6.12 - 2024-02-07

### Other

* do not normalized before writing
* bump to 0.6.12

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.6.11...v0.6.12

## 0.6.11 - 2024-01-24

### Other

* require python 3.7
* remove replace carriage return with new line
* bump to 0.6.11

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.6.10...v0.6.11

## 0.6.10 - 2024-01-17

### Other

* bump to 0.6.10 ([#461](https://github.com/randy3k/radian/pull/461))
* Update change log
* push to on tags

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.6.9...v0.6.10

## 0.6.9 - 2023-11-28

### Other

* Require prompt-toolkit 3.0.41 ([#451](https://github.com/randy3k/radian/pull/451))
* bump to 0.6.9

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.6.8...v0.6.9

## 0.6.8 - 2023-10-18

### Other

* use python codecov directly
* Add support for `ldpaths` detection on macOS via `DYLD_FALLBACK_LIBRARY_PATH` ([#417](https://github.com/randy3k/radian/pull/417))
* edit README ([#440](https://github.com/randy3k/radian/pull/440))
* do not set locale on windows ([#441](https://github.com/randy3k/radian/pull/441))

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.6.7...v0.6.8

## 0.6.7 - 2023-08-20

### Other

* set LC_CTYPE to en_US.UTF-8 if it is not set
* only change locate for R 4.2 windows
* bump to v0.6.7 ([#431](https://github.com/randy3k/radian/pull/431))
* require rchitect 0.4.1

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.6.6...v0.6.7

## 0.6.6 - 2023-06-02

### Other

* Use backported is_ascii ([#415](https://github.com/randy3k/radian/pull/415))
* Use simple ascii check instead ([#416](https://github.com/randy3k/radian/pull/416))
* bump to 0.6.6
* add a note about parallel computation

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.6.5...v0.6.6

## 0.6.5 - 2023-04-12

### Other

* only wrap text if the line length > 1000 ([#389](https://github.com/randy3k/radian/pull/389))
* Update README.md
* Check against R 4.1 instead
* implement ctrl_key_map option ([#409](https://github.com/randy3k/radian/pull/409))
* Update README.md
* force utf8 encoding when triming history
* use codecov action
* bump to 0.6.5

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.6.4...v0.6.5

## 0.6.4 - 2022-10-11

### Bug Fixes

* Fix multi bytes multi line strings ([#379](https://github.com/randy3k/radian/pull/379))

### Other

* add a faq for using unicode in windows and R 4.2+
* bump to 0.6.4

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.6.3...v0.6.4

## 0.6.3 - 2022-05-19

### Other

* getpass should return an R object
* add a test for getpass
* only set askpass if unset
* bump to 0.6.3

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.6.2...v0.6.3

## 0.6.2 - 2022-05-05

### Other

* set LANG to en_US.UTF-8 if not set for R 4.2 windows
* bump to 0.6.2

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.6.1...v0.6.2

## 0.6.1 - 2022-04-22

### Other

* strip ansi sequence
* check if text is empty in shell mode
* require at least prompt_toolkit 3.0.15
* bump to 0.6.1

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.6.0...v0.6.1

## 0.6.0 - 2022-02-25

### Bug Fixes

* fix ctrl-o
* fix vairous prompt related issues

### Other

* python 3 only
* require prompt_toolkit 3.0
* python 3 only
* require python 3.6
* improve key bindings
* remove python2 compatibility code
* allow not sticky_on_sigint
* ignore browser commands in history
* remove python 2.7 from appveyor
* make _last_working_index invisible to prompt
* use getpass in nested call
* use history_book to share history
* remove unused code
* convert Keys as is
* make sure radian has started
* remove librapay
* Bump to promot_toolkit 3.0 ([#318](https://github.com/randy3k/radian/pull/318))
* perhaps 0.6 is better
* EditingMode and InputMode enums handling ([#328](https://github.com/randy3k/radian/pull/328))
* trim history if it is too big
* avoid user from setting a small value of history_size
* only insert break once
* add silent flag
* update README
* do not offer switch
* wider screen
* use v2 actions
* unused os
* bump to radian 0.6.0

### Refactor

* refactor file structure

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.5.12...v0.6.0

## 0.5.12 - 2021-09-21

### Bug Fixes

* fix github action
* fix reticulate tests

### Other

* not needed
* remove circleci config
* Update README.md ([#283](https://github.com/randy3k/radian/pull/283))
* Merge branch 'master' of github.com:randy3k/radian
* show r version in job names
* also test python 2.7
* start 0.5.12.dev0
* bump to 0.5.12
* update CHANGELOG

### Testing

* test R 3.6

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.5.11...v0.5.12

## 0.5.11 - 2021-06-03

### Other

* Recommend python official distribution ([#239](https://github.com/randy3k/radian/pull/239))
* added conda install method
* Add instructions for installing jedi with conda ([#257](https://github.com/randy3k/radian/pull/257))
* Add conda-forge badge ([#258](https://github.com/randy3k/radian/pull/258))
* make sure the binary is intel based
* only needed for reticulate <1.18.9008
* refactor
* wrong note
* support jedi 0.18
* bump version
* more robust matching
* note for setuptools
* force pywinpty to 0.5.7
* support save flag
* updated R download url for mac
* install libpng
* use HOMEBREW_NO_AUTO_UPDATE
* check if jedi is imported
* use actions
* use github actions to upload tar ball
* use cancel-workflow-action
* bump to 0.5.11

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.5.10...v0.5.11

## 0.5.10 - 2021-02-05

### Other

* use GITHUB_PATH, ::add-path:: is defuncted
* use jedi 0.17.2
* upper bound jedi [ci skip]
* set the default value of `emacs_bindings_in_vi_insert_mode` to False
* bump to 0.5.10
* bound jedi
* enable
* update changelog

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.5.9...v0.5.10

## 0.5.9 - 2020-10-29

### Bug Fixes

* fix multiline raw string detection

### Other

* enable autosuggestion
* enable toggling of autosuggestion feature via radian.auto_suggest
* Enable autosuggestion from history ([#223](https://github.com/randy3k/radian/pull/223))
* Enable emacs keybindings to vi insert mode ([#227](https://github.com/randy3k/radian/pull/227))
* set default of `auto_suggest` to False as it doesn't play very well with reticulate
* bump rchitect requirement
* bump radian to 0.5.9

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.5.8...v0.5.9

## 0.5.8 - 2020-06-29

### Other

* need to force reticulate to use current python in tests
* require master rchitect
* force reticulate to use current python when testing
* set `RETICULATE_PYTHON` automatically when `force_reticulate_python`
* better switching handling
* add a line break
* bump to 0.5.8
* use readline instead
* default to "no"
* bump rchitect requirement
* upgrade target radian to current version

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.5.7...v0.5.8

## 0.5.7 - 2020-06-24

### Bug Fixes

* Fix XDG config default path ([#205](https://github.com/randy3k/radian/pull/205))

### Other

* prompt to switch python runtime
* instruct user to open radian manually on windows
* support dev version
* bump to prerelease
* option to force current python runtime
* do not use quiet flag
* Update setup.py
* Update setup.py ([#203](https://github.com/randy3k/radian/pull/203))
* no spaces
* bump to 0.5.7

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.5.6...v0.5.7

## 0.5.6 - 2020-06-17

### Other

* use XDG_CONFIG_HOME instead of XDG_DATA_HOME
* clarification
* updated changelog
* bump to 0.5.6

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.5.5...v0.5.6

## 0.5.5 - 2020-06-16

### Other

* radian.completion_adding_spaces_around_equals
* allow codecov in prs
* do not need libffi6
* use git --version instead
* make library/require completion faster
* some refactor
* improve multiline test
* respect the `highlight_matching_bracket` setting in python prompt
* use RADIAN_NO_INPUTHOOK instead
* rename function
* allow custom history path
* rename history_path to history_location
* different settings for global/local history file
* read both local and global profile if both exist
* load both global and local profiles if they both exist
* bump to 0.5.5
* global profile should be in home directory

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.5.4...v0.5.5

## 0.5.4 - 2020-05-02

### Bug Fixes

* fix note

### Other

* figured out the culprit
* longer timeout
* remove unused variable
* bump min requirement of rchitect
* use git url
* support custom vi prompt
* use abbr
* catch radian profile loading error
* explictly use register_signal_handlers [ci skip]
* the workaround for microsoft store python is in place
* bump to 0.5.4

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.5.3...v0.5.4

## 0.5.3 - 2020-04-22

### Other

* use rchitect.interface.peek_event
* use polled_events
* updated README
* a workaround for the slow completion of "print"
* require rchitect 0.3.23
* bump to 0.5.3
* disable complete while typing in 'print()'

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.5.2...v0.5.3

## 0.5.2 - 2020-04-20

### Bug Fixes

* fix typo

### Other

* disable sigint when processing events
* added flag to support profiling
* bump to 0.5.2

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.5.1...v0.5.2

## 0.5.1 - 2020-04-19

### Other

* suppress stderr when checking parse_text
* added changelog
* Revert "remove completion.timeout"
* workaround to not trigger completions when loading packages
* bump to 0.5.1

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.5.0...v0.5.1

## 0.5.0 - 2020-04-19

### Other

* initial support of R 4.0 raw strings
* start dev cycle
* remove debug code
* factor cursor_in_string
* support R_BINARY via --r-binary
* let rchitect check the file
* autocomplete in string
* remove completion.timeout
* tag 0.5.0

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.4.9...v0.5.0

## 0.4.9 - 2020-04-09

### Other

* apply strip
* check completion is not token
* require 0.1.5
* exclude tests
* bump to 0.4.9

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.4.8...v0.4.9

## 0.4.8 - 2020-03-17

### Bug Fixes

* fix typo ([#166](https://github.com/randy3k/radian/pull/166))

### Other

* actually need buffering in python 2
* process events in cook mode
* detach input
* better support later::later
* do not echo text while processing events
* bump to 0.4.8
* do not enable line mode
* suppress quartz error message
* do not run inputhook in ci
* require rchitect 0.3.19
* do not check the first line
* write some random text before sigint

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.4.7...v0.4.8

## 0.4.7 - 2020-02-28

### Other

* support history_search_ignore_case
* accept options as dummy
* run user hooks when loaded
* use SUPPRESS_ to suppress stdio on Windows
* flush console after completion
* use .package
* use ConEmuANSI as a workaround
* APPVEYOR doens't like these flags
* use CMDER_ROOT instead
* do not use partial matching
* bump to 0.4.7

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.4.6...v0.4.7

## 0.4.6 - 2020-02-09

### Other

* fallback to `input` if `read_console` is called nestedly
* add a reference to prompt_toolkit
* use ANSICON on windows instead of crayon.enabled
* bump to v0.4.6

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.4.5...v0.4.6

## 0.4.5 - 2020-02-05

### Other

* no longer the case
* consistant ansi color
* point to radian instead
* use lineedit 0.1.4.dev0
* simplify REPL
* simplify output code
* bump requirements
* use print_formatted_text to support ANSI sequences in older Windows
* enable crayon on windows terminals
* enable edit in editor
* use our own keybind c-x c-e
* match R's edit behavior
* it should be radian
* increase default timeout
* support askpass
* add radian.highlight_matching_bracket
* bump to 0.4.5

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.4.4...v0.4.5

## 0.4.4 - 2019-12-19

### Bug Fixes

* fix python 2 issue
* fix path issues

### Other

* a note about microsoft store python
* latex completions
* python 2.7 fix
* support latex completions in reticulate mode
* require python 2.7 or python 3.5+
* requires rchitect 0.3.15
* use output from session directly
* catch error in return
* requires rchitect 0.3.16.dev1
* start 0.4.4.dev0
* use add-path
* use conda activate
* use sys.stdout instead
* release 0.4.4

### Refactor

* refactor github actions config

### Testing

* test circleci windows setup

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.4.3...v0.4.4

## 0.4.3 - 2019-12-10

### Bug Fixes

* fix changelog
* fix indentation

### Other

* insert a space before equal sign
* extra space after equal sign
* run R with vanilla
* bump rchitect to 0.3.12
* use powershell to install R
* Update CHANGELOG
* github actions windows-2019 doesn't like (24, 80)
* to windows-latest
* update note about profile [ci skip]
* only serach in tests dir
* load R_LD_LIBRARY_PATH from ldpaths
* use shell
* make sure libPath in R_LD_LIBRARY_PATH
* load R_LD_LIBRARY_PATH from ldpaths ([#126](https://github.com/randy3k/radian/pull/126))
* github actions on pull_request
* update github actions config
* requires rchitect 0.3.14
* bump to 0.4.3

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.4.2...v0.4.3

## 0.4.2 - 2019-10-10

### Bug Fixes

* fix mac r install script

### Other

* use github actions
* add github actions badge
* build matrix
* use less github actions
* use less github actions
* debug failed test
* pytest -s
* add a comment about windows-latest
* make sure type is correct
* bump to 0.4.2
* use os._exit to force quit
* special handle for carriage return
* bump to 0.4.2
* don't ask

### Testing

* test different pythons
* test all matrix builds in github actions

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.4.1...v0.4.2

## 0.4.1 - 2019-09-17

### Bug Fixes

* fix README
* fix python2 issue

### Other

* always insert new line
* bump rchitect requirement
* install python 3.4 from conda-forge
* colorize stderr messages
* typo
* Update stderr_format
* stderr coloring for unix only
* use print_formatted_text from prompt_toolkit
* check if cursor is at an empty line
* add readline test
* bump rchitect requirement
* bump to 0.4.1
* bump rchitect requirement again
* add vi mode state in prompt
* add spaces around escaped key
* increase timeout for shell completion
* allow vi mode state in all modes
* tab again in case it missed
* support .radian_profile
* many typos
* allow arbitray path to .radian_profile
* allow -q flag
* Added custom R lexer for better colour ([#113](https://github.com/randy3k/radian/pull/113))
* bump rchitect requirement
* more news
* update package_data
* settings refactoring
* do not need default_prompt
* settings are not preserved, pass the settings to the session directly
* remove unused import

### Refactor

* refactor reticulate code
* refactor console code

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.4.0...v0.4.1

## 0.4.0 - 2019-05-12

### Bug Fixes

* fix imports
* fix shell cd tests

### Other

* update miniconda link [ci skip]
* .
* more refactor
* reticulate prompt
* python2 fix
* require rchitect>=0.3.0.dev0
* pytest -s
* delete py_config.py
* refactor
* minor refactor
* update rchitect dependency
* remove the reticulate repl trigger
* allow R devel to fail
* do not add :: if in string
* cache preceding and following text filters
* update options doc
* remove LD_LIBRARY_PATH note
* shared library note [ci skip]
* key binding update
* make sure key is a list
* allow custom keys
* set eager
* add v0.4.0 changelog
* support mapping all keys (unsafe and not documented)
* don't install rchitect and lineedit from github
* new version of rchitect requires compilation
* update ci configs
* python 2 fixes
* update circleci
* work with coverage
* add coverage badge
* cosmetic changes
* improve coverage
* simplify the cleanup logic
* wait until radian starts
* add more shell tests
* check main.cleanup explictly
* install jedi in ci
* longer timeout
* bump requirement of rchitect
* indent python code if previous char is colon
* improve multiline tests
* bump to v0.4.0

### Refactor

* refactor reticulate keybindings loading code
* refactor hooks into individual functions
* refactor tests
* refactor tests

### Testing

* test shell mode
* test reticulate mode
* test reticulate multiline code

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.3.4...v0.4.0

## 0.3.4 - 2019-03-12

### Bug Fixes

* fix #86

### Other

* FileNotFoundError is python 3 only
* readline error
* bump to 0.3.4

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.3.3...v0.3.4

## 0.3.3 - 2019-03-08

### Other

* lower bound pyte
* support python setup.py test
* factor out tests_deps
* warn users not to copy the whole configuration
* fixme: longjmp
* patch reticulate directly
* move locals and globals in function so reticulate is not initialized
* remove rtichoke reference
* why radian
* bump to 0.3.3

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.3.2...v0.3.3

## 0.3.2 - 2019-02-25

### Other

* upper bound dependencies
* next dev build
* Update README.md
* get R_SHARE_DIR etc from R if they don't exist
* catch subprocess.CalledProcessError
* bump to 0.3.2

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.3.1...v0.3.2

## 0.3.1 - 2018-12-28

### Bug Fixes

* fix reticulate repl completion error

### Other

* update badges
* Merge branch 'radian'
* Update README.md
* update logo
* lower bound rchitect
* bump to v0.3.1
* remove old code

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.3.0...v0.3.1

## 0.3.0 - 2018-12-18

### Bug Fixes

* fix version test

### Other

* use rchitect
* update badages
* reband as radian
* remove rtichoke naming credit
* update readme
* add logo

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.2.14...v0.3.0

## 0.2.14 - 2018-12-16

### Bug Fixes

* fix .pythonapi masking issue

### Other

* bump to 0.2.14

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.2.13...v0.2.14

## 0.2.13 - 2018-12-16

### Bug Fixes

* fix typo completion_timeout

### Other

* disable .py namespace due to recent changes of R upstream
* namespace is depreated, use .pythonapi env
* .py namespace is deprecated
* bump to 0.2.13

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.2.12...v0.2.13

## 0.2.12 - 2018-08-30

### Bug Fixes

* fix backspace deletion

### Other

* bump to v0.2.12

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.2.11...v0.2.12

## 0.2.11 - 2018-08-29

### Other

* remove unused rexec
* update the usage of os.execv
* determine how the script is executed
* bump to 0.2.11

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.2.10...v0.2.11

## 0.2.10 - 2018-08-29

### Other

* enable_suspend
* bump to 0.2.10

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.2.9...v0.2.10

## 0.2.9 - 2018-08-29

### Other

* use try to catch error instead of rexec
* bump version of rapi

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.2.8...v0.2.9

## 0.2.8 - 2018-08-27

### Other

* add 0.2.7 note
* add quiet option
* bump to 0.2.8

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.2.7...v0.2.8

## 0.2.7 - 2018-08-22

### Other

* support R_LD_LIBRARY_PATH
* bump to 0.2.7

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.2.6...v0.2.7

## 0.2.6 - 2018-08-21

### Other

* allow non-empty LD_LIBRARY_PATH
* bump to 0.2.6

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.2.5...v0.2.6

## 0.2.5 - 2018-08-18

### Other

* do not use travis to deploy [ci skip]
* new option `indent_lines`
* bump to v0.2.5

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.2.4...v0.2.5

## 0.2.4 - 2018-08-13

### Other

* add backspace to exit reticulte repl mode
* add a short note about libR
* do not pass `--restore-data` to R
* bump to v0.2.4

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.2.3...v0.2.4

## 0.2.3 - 2018-08-12

### Other

* better auto match quotation
* install py namespace
* bump to 0.2.3

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.2.2...v0.2.3

## 0.2.2 - 2018-08-10

### Other

* add donation badges
* check the emptyness of data
* bump lineedit
* update changelog for the new release

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.2.1...v0.2.2

## 0.2.1 - 2018-06-28

### Other

* Update README.md
* R-release appveyor test
* bump minimum requirement of rapi
* bump to 0.2.1

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.2.0...v0.2.1

## 0.2.0 - 2018-06-17

### Bug Fixes

* fix bracketed paste mode
* fix search display bug
* fix prase_text_complete bug
* fix R_interrupts_pending

### Other

* move R bits to rapi
* add minimal changelog
* ensure path first
* use rapi defaults callback
* make encoding safe
* pass command line args to R
* add debug flag
* do not tic
* move result_from_prompt to get_prompt
* use markdown readme
* move prompt related code to lineedit
* dont' need the ugly hack
* don't need pandoc
* util is not needed
* redirect stderr when try parsing
* shell mode
* bump min version of lineedit
* do not insert new line for readline mode
* make sure lexer is None
* esc enter only insert new line in mutliline mode
* move mode detection out of while loop
* bump rapi to 0.0.6
* bump to 0.0.3
* browse mode and r mode share history
* simplify create_read_console
* bump rapi and lineedi versions
* missing unicode_literals
* rcopy to text_type
* set encoding
* use getpreferredencoding
* call our own callbacks
* set rapi encoding
* remove rapi set_encoding
* better unicode support
* some level of unicode support on windows
* add error handler
* fully support unicode
* only need wctomb
* add system2utf8
* full support
* these functions have renamed
* bump rapi to 0.0.9
* enable_history_search
* only completion startswith token
* do not use readline
* only on unix
* latest rapi codebase
* add note for reticulate error
* honor complete_while_typing
* add rtichoke namespace
* bump rapi
* ask_input which is compatible with python 2 and 3
* call installed.pacakge from utils
* use tryCatch to run completion
* do not use default callbacks
* everything in devel
* requires 0.0.12
* allow registering custom mode
* highlight reticulate prompt
* improve reticulate mode
* reticulate mode
* improve retichoke code parsing
* backup settings
* .py::import
* use import_builtins
* revert back to .py
* use import_builtins
* tilde to activate repl_python
* add note for reticulate mode
* activate reticulate repl in r mode
* quiet if reticulate was loaded
* rtichoke.enable_reticulate_prompt to enable/disable reticulate repl mode
* break long setting docs
* better wording
* do not export machine and session
* insert new line only when the buffer is not empty
* ctrl-d to exit reticulate mode
* reset interrupted status
* do not save history when entering/leaving reticulate mode
* unindent block code
* remove unneccessry import
* use jedi to do autocompletion in reticulate mode
* evaluate the reticulate code in a sandbox
* do not use backslashreplace
* continue upon syntax error
* bump versions of rapi and lineedit
* add tests
* rversion2 has been renamed
* add docker note
* bump rapi requirement
* use contextmanager
* add test for rtichoke --version
* respect LD_LIBRARY_PATH
* bump rapi
* update Makefile
* use an empty parent
* return process for writing
* change default to monokai
* version 0.2.0

### Refactor

* refactor mode activation
* refactor reticulate register code
* refactor __init__ and __main__

### Testing

* test again 2.7 and 3.5

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.1.9...v0.2.0

## 0.1.9 - 2018-05-02

### Other

* start to 0.1.9.dev0
* unit is second
* only set history_search_text at the working index
* meta enter to insert new line
* Update README
* add note for loading library
* or upgrade readline
* suppressWarnings when cancelling completion
* bump to 0.1.9

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.1.8...v0.1.9

## 0.1.8 - 2018-04-29

### Bug Fixes

* fix search highlight bug

### Other

* start 0.1.8.dev0
* add pypi badge
* completion timeout
* improve completion timeout
* set default to 0.05
* move create_prompt_bindings to modalprompt
* check insert_new_line when ^C
* redraw layout when stdout.flush() returns an error
* more note to setTimeLimit
* bump to 0.1.8

### Refactor

* refactor into rtichokeprompt

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.1.7...v0.1.8

## 0.1.7 - 2018-04-27

### Bug Fixes

* fix cancel completion bug

### Other

* start 0.1.7.dev0
* Update prompt-toolkit
* output byte data to STDOUT directly
* convert MSCS to string
* bump to 0.1.7

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.1.6...v0.1.7

## 0.1.6 - 2018-04-11

### Bug Fixes

* fix #48

### Other

* break curly braces when auto_match is True
* start 0.1.5.dev0
* bump to 0.1.6

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.1.5...v0.1.6

## 0.1.5 - 2018-04-10

### Other

* only reset when completions is empty
* bump to 0.1.5

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.1.4...v0.1.5

## 0.1.4 - 2018-04-10

### Bug Fixes

* fix completion keys
* Fix: reset complete_state when there are no completions

### Other

* start 0.1.4.dev0
* use --ask-save instead of --save
* update prompt-toolkit
* bump to 0.1.4

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.1.3...v0.1.4

## 0.1.3 - 2018-04-01

### Other

* credit prompt_toolkit
* use ANSI color_depth for basic terminal
* update introduction
* check output_width > 0
* start dev version
* update prompt-toolkit
* remove rice
* support --save and --restore-data
* use SA_NOSAVE and SA_SAVE
* bump to 0.1.3

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.1.2...v0.1.3

## 0.1.2 - 2018-02-26

### Other

* add banner
* update rtichoke.png
* update prompt_toolkit
* only reset eventloop when app is running
* bump to v0.1.2

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.1.1...v0.1.2

## 0.1.1 - 2018-02-23

### Bug Fixes

* fix typo

### Other

* start next dev version
* update prompt-toolkit
* a hack to resolve #35
* more traceback for debugging
* rename rtichoke
* mroe rename
* bump to 0.1.1

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.43...v0.1.1

## 0.0.43 - 2018-02-15

### Bug Fixes

* fix python 2 error

### Other

* start 0.0.43 dev
* Update README.md
* move R_HOME detection to __init__.py
* add r executable and version in -v
* use single quote
* normalize path
* use R --version
* forward stderr to stdout
* NA r_version when r_home is empty
* add libR dir to PATH on windows
* bump to 0.0.43
* search again using registry
* use latin-1 as default in Windows
* use msvcrt to change PATH

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.42...v0.0.43

## 0.0.42 - 2018-02-07

### Bug Fixes

* fix RICE_COMMAND_ARGS underscopes

### Other

* start 0.0.42.dev1
* use try to evaluate completeToken
* only remove pair when auto_match is TRUE
* update prompt-toolkit
* added an environment vairable RICE_COMMAND_ARGS
* update prompt-toolkit
* update prompt-toolkit
* bump to 0.0.42

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.41...v0.0.42

## 0.0.41 - 2018-01-22

### Other

* improve greeting message
* start next dev build
* update prompt toolkit and disable _start_timeout() in key processor
* update prompt-toolkit
* bugfix on flushing using prompt-toolkit
* bump to 0.0.41

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.40...v0.0.41

## 0.0.40 - 2017-12-30

### Documentation

* doc the settings

### Other

* new option for not inserting new line
* better startup newline print
* update prompt-toolkit
* auto match brackets and quotes
* do not auto match when in quotations
* update insert auto match filters
* only R args in Nvim-R
* remote note to reticulate
* remove the note for bracketed paste mode
* restrict the auto match scope
* update prompt toolkit code
* remove unneccessary import
* don't detect via registry
* update note for R_HOME
* bump to 0.0.40

### Refactor

* refactor modalprompt

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.39...v0.0.40

## 0.0.39 - 2017-12-05

### Other

* make sure token is non empty
* improve package name completion
* bump to 0.0.39

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.38...v0.0.39

## 0.0.38 - 2017-11-22

### Other

* use PYFUNCTYPE to keep GIL
* bump to 0.0.38

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.37...v0.0.38

## 0.0.37 - 2017-11-13

### Bug Fixes

* fix search control label
* fix garbage collection issue

### Other

* use R_ToplevelExec to evaluate R_ParseVector as R_ParseVector may longjmp
* revert R_ToplevelExec approach
* use R_tryCatchError to evaluate R_ParseVector
* requires R 3.4.0 or above
* print error when terminal doesn't support unicode
* use rc.settings ipck
* cache the list of installed packages
* a more efficient way to get installed package list
* unprotect earlier
* remove unused module
* print empty line after changing directory
* clean also pyc files
* update prompt_toolkit
* adapt to new update of prompt_toolkit
* search no duplicates
* improve _search note
* remove the debug code
* python 2 fix
* pass status as reference
* bump to 0.0.37

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.36...v0.0.37

## 0.0.36 - 2017-10-24

### Other

* wrong last working index
* set history search text to empty string
* bump to 0.0.36

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.35...v0.0.36

## 0.0.35 - 2017-10-17

### Other

* libR_dir first
* windows python 2 support
* bump to 0.0.35

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.34...v0.0.35

## 0.0.34 - 2017-10-17

### Other

* add libR_dir to PATH on Windows
* use registry to find R
* bump to 0.0.34

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.33...v0.0.34

## 0.0.33 - 2017-10-13

### Other

* improve readme
* unneccessary create_layout
* bump to 0.0.33

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.32...v0.0.33

## 0.0.32 - 2017-10-05

### Other

* enable ctrl-o in emacs mode
* enable history search using up and down
* more reserve space
* c-c to cancel autocompletion
* replace backslash in reticulate_set_message
* shell mode history saved multiple times
* improve accept_handler
* double escape not exit auto completion anymore
* remove unused methods
* bump to 0.0.32

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.31...v0.0.32

## 0.0.31 - 2017-10-04

### Bug Fixes

* fix bracketed paste mode

### Other

* return double backslashes
* customizable browse prompt
* tab to insert space when buffer is empty
* bump to 0.0.31

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.30...v0.0.31

## 0.0.30 - 2017-10-04

### Other

* set encoding first
* check width less frequently
* better handle escape sequence
* empty \U \u are also invalid
* api.encoding is now platform sensitive
* empty backtick pair is invalid
* completeToken may raise error
* null char is also invalid
* \` is valid
* improve search for invalid chars
* bump to 0.0.30

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.29...v0.0.30

## 0.0.29 - 2017-10-03

### Bug Fixes

* fix more encoding issues

### Other

* update reticulate note
* note to reticulate rice users
* use packageStartupMessage
* bump to 0.0.29

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.28...v0.0.29

## 0.0.28 - 2017-09-28

### Other

* set RETICULATE_PYTHON to current executable
* add note for reticulate
* start 0.0.27-dev
* detect if dependencies_loaded
* more robust browse prompt
* always pass `--no-restore-data`
* bump to 0.0.28

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.27...v0.0.28

## 0.0.27 - 2017-09-26

### Bug Fixes

* fix browe prompt space

### Other

* browse prompt support
* use a local history if it exists
* --no-history --local-history and --global-history
* add note to history file
* bump to 0.0.27
* use boolean
* encoding using codepage in windows
* catch error in shlex.split
* make return clearer
* more explict match for browse mode
* use PyDLL

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.26...v0.0.27

## 0.0.26 - 2017-09-23

### Bug Fixes

* fix resize bug

### Other

* the upstream windows bug has been fixed
* honor the option `setWidthOnResize`
* dont print cpr not support warning
* from __future__ import unicode_literals
* add auto_width option
* use auto_width
* poll terminal width
* auto width feature
* bump to 0.0.26

### Refactor

* refactor modalprompt

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.25...v0.0.26

## 0.0.25 - 2017-09-22

### Other

* use U flag
* change default shell prompt
* update screenshort
* update default shell prompt setting
* bump to 0.0.25

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.24...v0.0.25

## 0.0.24 - 2017-09-21

### Other

* flushed a wrong device
* customize tab size
* too many deletion
* bump to 0.0.24

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.23...v0.0.24

## 0.0.23 - 2017-09-21

### Other

* backeted paste mode should evaluate
* do not copy margin when auto indentation is off
* bump to 0.0.23

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.22...v0.0.23

## 0.0.22 - 2017-09-21

### Bug Fixes

* fix #19

### Other

* flush stdout and stderr
* bump version

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.21...v0.0.22

## 0.0.21 - 2017-09-20

### Other

* improve readline interrupt spacing
* use c-j
* delete indentation
* multicolumn completion menu
* package completion needs at least one letter
* double escape to hide autocompletion
* custom shell mode prompt
* improve prompt detection
* option complete_while_typing and various bugfix
* show completion menu when trigger explictily
* bump version

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.20...v0.0.21

## 0.0.20 - 2017-09-19

### Other

* disable menu
* better history support
* bump version
* further simplication
* readline mode sigint
* append to history if mode is different

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.19...v0.0.20

## 0.0.19 - 2017-09-18

### Bug Fixes

* fix windows encoding issue

### Other

* date -> time
* don't print ms
* don't append history in readline mode
* shell model enables history
* bump version

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.18...v0.0.19

## 0.0.18 - 2017-09-18

### Other

* don't spam me
* improve shell mode history
* bump version

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.17...v0.0.18

## 0.0.17 - 2017-09-18

### Bug Fixes

* fix readline bug
* fix vi key movement

### Other

* not use history file
* update
* do not erase_when_done
* simplify multiprompt
* more simplification
* bump version

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.16...v0.0.17

## 0.0.16 - 2017-09-17

### Other

* auto completion path in shell mode
* improve path completion
* better windows path completion support
* missing ctypes
* don't use ctypes
* improve shell mode lexer
* support cd -
* improve README.md
* improve cd
* improve completion of path in quotes
* use slash instead of backslash on windows
* RiceApplication
* directory only when cd
* relative to dirname
* R HOME contains RHOME
* first step to customize application
* no more set_prompt_mode
* bump version

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.15...v0.0.16

## 0.0.15 - 2017-09-15

### Other

* install pandoc
* tidy up codebase
* make emacs mode more robust
* rename as app_initialize
* new feature: shell mode
* only do shlex.split on posix
* update screenshot and add shell mode to the feature list
* do not always send email [ci skip]
* bump version

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.14...v0.0.15

## 0.0.14 - 2017-09-14

### Bug Fixes

* fix #11

### Other

* use lower case rice
* acccept --vanilla etc
* another small r
* remove debug code
* allow to disable auto indentation
* new setting rice.prompt
* add .travis.yml
* auto deplay when tagged
* bump version

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.13...v0.0.14

## 0.0.13 - 2017-09-14

### Bug Fixes

* fix completion issue in #9
* fix the prompt again

### Other

* allow custom prompt
* forgot to remove debug code
* don't use crazy prompt
* disable complete_while_typing in other prompts
* strip PROMPT space
* use flags in installation
* bump version

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.12...v0.0.13

## 0.0.12 - 2017-09-13

### Other

* recommend python 3
* enter to select completion item
* only when started completion
* update prompt_toolkit
* Update README.md ([#8](https://github.com/randy3k/radian/pull/8))
* Merge branch 'master' of github.com:randy3k/ride
* make sure it is a string
* disable the warning for now
* bump version

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.11...v0.0.12

## 0.0.11 - 2017-09-12

### Bug Fixes

* fix python 2

### Other

* bump version

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.10...v0.0.11

## 0.0.10 - 2017-09-10

### Other

* add alias note
* move keybindings to file
* add note to conda libreadline
* improve autocompletions
* options default value
* remove object viewer
* add note for python2.7 on windows
* add an env variable RICE_VERSION
* when if the app is dummy
* repect windows encoding
* bump to 0.0.10

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.9...v0.0.10

## 0.0.9 - 2017-09-04

### Other

* rice
* vi editing mode and custom color shceme
* remove the archive files
* read more than 4096 bytes
* add a note about prompt_toolkit
* complete package names
* bump to 0.0.9

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.8...v0.0.9

## 0.0.8 - 2017-09-04

### Other

* add vi editing mode
* add note to LD_LIBRARY_PATH
* better history navigation
* add Nvim-R setup
* update prompt_toolkits
* remove unused variables
* remove c-c key
* update nvim-R note
* some lint fixes
* add control J keybind
* check if app is dummy
* nvim-r no highlight
* not partially
* bump to 0.0.8

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.7...v0.0.8

## 0.0.7 - 2017-08-23

### Other

* add help menu
* Update README.md
* auto indent on braces and brackets
* tab to indent
* bump to 0.0.7

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.6...v0.0.7

## 0.0.6 - 2017-08-17

### Other

* catch all errors
* bump to 0.0.6

**Full Changelog**: https://github.com/randy3k/radian/compare/v0.0.5...v0.0.6

## 0.0.5 - 2017-08-17

### Bug Fixes

* fix up buttom in input buffer
* fix bug to use R_HOME
* fix command name

### Other

* init repo
* enable completions
* find libR
* Update README.md
* typo
* always save history to user directory
* improve completions and various typos
* improve brackted paste mode
* improve libR searching
* rename as Role
* Update README.md
* Update .gitignore
* Update LICENSE.md
* change debug prompt to control y
* better history navigation
* add long description
* only use text before cursor in autocompletion
* enable syntax highlight
* show parse error message
* help modes
* Update README.md
* ControlH also exits help modes
* use pypandoc to convert md to rst
* add screenshot
* Update README.md
* bump version
* Update list
* show help for non-empty string only
* don't parse block code and tab to space
* strip code after execution
* show warnings as they appear
* update
* move prompt_toolkit files
* move to Rf_initialize_R
* update prompt_toolkit
* make working
* add styles
* works on completion and multi prompt
* update prompt_toolkit
* rename as Rice
* update screenshot
* tag 0.0.1
* update prompt_toolkit
* use find_packages()
* use unicode_literals
* update .gitignore
* Update README.md
* bump to 0.0.3
* add 🍚
* enable suspend by c-z
* update prompt_toolkit
* bracketed paste mode
* Update README.md
* Update README.md
* working towards windows support
* run on windows now
* more code around
* bump version
* works on windows
* allow custom prompt from R
* only execute successfully parsed code
* update README.md
* history file should be .rice_history
* Update README.md
* bump to 0.0.5

### Refactor

* refactor code into modules

<!-- generated by git-cliff -->
