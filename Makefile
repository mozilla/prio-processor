all:
	cd libprio && CCFLAGS='-fPIC' scons && cd ..
	mkdir -p build
	swig -python -outdir prio -o libprio_wrap.c libprio.i
	python3 setup.py build_ext

clean:
	cd libprio && scons -c && cd ..
	find . \( \
		-name "*.pyc" \
		-o -name "*.so" \
		\) -delete
	find . \( \
		-name "__pycache__" \
		-o -name "*.egg-info" \
		-o -name "htmlcov" \
		\) -exec rm -r {} +
	rm -rf build

test:
	pipenv sync --dev
	pipenv run pytest

coverage:
	pipenv run coverage report
