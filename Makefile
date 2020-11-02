
all: test install

testupload: dist
	twine upload --repository testpypi dist/*

upload: dist
	twine upload dist/*

install:
	pip install .

test:
	python -m unittest

dist: clean
	python setup.py sdist bdist_wheel

clean:
	-rm -rf dist/ build/ seutil.egg-info/
