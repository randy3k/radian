all:

clean:
	rm -rf build dist *.egg-info .pytest_cache && \
	find . -name '*.so' -not -path './.venv/*' -exec rm -rf {} \; &&\
	find . -name '*.o' -not -path './.venv/*' -exec rm -rf {} \; &&\
	find . -name '*.pyc' -not -path './.venv/*' -exec rm -rf {} \;

dev-changelog:
	git cliff -o

changelog:
	git cliff --bump -o
