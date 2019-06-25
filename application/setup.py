from distutils.core import setup

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="prio-processor",
    version="0.1",
    description="A processing engine for prio data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Anthony Miyaguchi",
    author_email="amiyaguchi@mozilla.com",
    url="https://github.com/mozilla/prio-processor",
    entry_points={"console_scripts": ["prio-processor=prio-processor.__main__:main"]},
    install_requires=["click"],
    packages=["prio-processor"],
)