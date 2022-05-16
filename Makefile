
all: test install

testupload: dist
	twine upload --repository testpypi dist/*

upload: dist
	twine upload dist/*

install:
	pip install .

test:
	pytest

dist: clean
	python setup.py sdist bdist_wheel

clean:
	-rm -rf dist/ build/ seutil.egg-info/

docs: clean
	python -m sphinx -b html -W --keep-going docs/source docs/build
