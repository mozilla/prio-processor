all:
	cd libprio && CCFLAGS='-fPIC' scons && cd ..
	mkdir -p build
	swig -python -outdir prio/lib -o libprio_wrap.c libprio.i
	python3 setup.py build_ext --build-lib prio/lib

clean:
	cd libprio && scons -c && cd ..
	rm *.so *.pyc

test:
	pipenv run coverage run -m pytest tests/

coverage:
	pipenv run coverage report