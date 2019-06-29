from setuptools import setup

setup(
    name="prio_processor",
    version="0.1",
    description="A processing engine for prio data",
    long_description_content_type="text/markdown",
    author="Anthony Miyaguchi",
    author_email="amiyaguchi@mozilla.com",
    url="https://github.com/mozilla/prio-processor",
    install_requires=["click", "pyspark >= 2.4.0"],
    packages=["prio_processor"],
)
