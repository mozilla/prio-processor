from setuptools import setup

setup(
    name="prio_processor",
    version="1.3.0",
    description="A processing engine for prio data",
    long_description_content_type="text/markdown",
    author="Anthony Miyaguchi",
    author_email="amiyaguchi@mozilla.com",
    url="https://github.com/mozilla/prio-processor",
    entry_points={"console_scripts": ["prio-processor=prio_processor.__main__:entry_point"]},
    install_requires=["click", "gcsfs == 0.2.3", "pyspark >= 2.4.0"],
    packages=["prio_processor"],
)
