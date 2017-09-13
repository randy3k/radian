update-deps:
	cd rice/deps && \
	rm -rf prompt_toolkit && \
	svn export https://github.com/jonathanslenders/python-prompt-toolkit/branches/2.0/prompt_toolkit
