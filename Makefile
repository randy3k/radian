all:

clean:
	rm -rf build dist *.egg-info .pytest_cache && \
	find . -name '*.so' -not -path './.venv/*' -exec rm -rf {} \; &&\
	find . -name '*.o' -not -path './.venv/*' -exec rm -rf {} \; &&\
	find . -name '*.pyc' -not -path './.venv/*' -exec rm -rf {} \;


changelog:
	git-changelog --convention angular --sections feat,fix,refactor,chore,docs,revert,test \
		--provider github --output CHANGELOG.md
