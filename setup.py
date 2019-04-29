# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import setuptools
from distutils.core import setup, Extension
from glob import glob
from os import path


this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


extension_mod = Extension(
    "_libprio",
    ["libprio_wrap.c"],
    library_dirs=[
        "libprio/build/prio",
        "libprio/build/mpi",
    ],
    include_dirs=["/usr/include/nspr", "/usr/include/nss"],
    libraries=["mprio", "mpi", "nss3", "nspr4", "msgpackc"],
)

setup(
    name="prio",
    version = "0.3",
    description = "An interface to libprio",
    long_description = long_description,
    long_description_content_type='text/markdown',
    author = "Anthony Miyaguchi",
    author_email = "amiyaguchi@mozilla.com",
    url = "https://github.com/acmiyaguchi/python-libprio",
    packages = ["prio"],
    ext_modules=[extension_mod],
)
