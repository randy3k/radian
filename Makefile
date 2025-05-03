all:

clean:
	rm -rf build dist *.egg-info .pytest_cache && \
	find . -name '*.pyc' -exec rm -f {} \;
	find . -d -name *.o -exec rm -rf {} \; &&\
	find . -d -name *.so -exec rm -rf {} \; &&\
	find . -d -name __pycache__ -exec rm -rf {} \; &&\
	find . -d -name *.pyc -exec rm -rf {} \;
