all:
	mkdir -p build
	swig -python -outdir prio/lib -o libprio_wrap.c libprio.i
	python3 setup.py build_ext --build-lib prio/lib

clean:
	rm *.so *.pyc

test:
	coverage run -m pytest tests/

coverage:
	coverage report
