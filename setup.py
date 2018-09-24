# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from distutils.core import setup, Extension
from glob import glob

extension_mod = Extension(
    "_prio",
    ["libprio_wrap.c"],
    library_dirs=[
        "libprio/build/prio",
        "libprio/build/mpi",
    ],
    include_dirs=["/usr/include/nspr4", "/usr/include/nss3"],
    libraries=["mprio", "mpi", "nss3", "nspr4", "msgpackc"],
)

setup(
    name="prio",
    version = "0.1",
    description = "An interface to libprio",
    author = "Anthony Miyaguchi",
    author_email = "amiyaguchi@mozilla.com",
    url = "https://github.com/acmiyaguchi/python-libprio",
    packages = ["prio"],
    ext_modules=[extension_mod],
)
