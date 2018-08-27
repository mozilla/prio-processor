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
    include_dirs=["/usr/include/nspr4"],
    libraries=["mprio", "mpi", "nss3", "nspr4", "msgpackc"],
)
setup(name="prio", ext_modules=[extension_mod])
