all:

clean:
	find . -d -name __pycache__ -exec rm -rf {} \; &&\
	find . -d -name *.pyc -exec rm -rf {} \;
