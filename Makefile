all:
	swig -python libprio.i
	python3 setup.py build_ext --inplace

clean:
	rm *.so *.pyc *.c

