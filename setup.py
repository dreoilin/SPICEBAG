#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import setuptools
from numpy.distutils.core import setup, Extension

exts = [
        Extension('LINALG', ['turmeric/FORTRAN/LINALG.f90'])
        ]

setup(
	name='turmeric',
    install_requires=['numpy>=1.1.0', 'scipy>=1.0.0',
                      'tabulate>=0.7.3'],
    packages=setuptools.find_packages(),
    zip_safe=False,
    author="COD, TOR, JD",
    author_email="cian.odonnell@ucdconnect.ie",
    description="SPICE-like circuit simulator \
                    with FORTRAN numerical subroutines",
    ext_modules = exts,
    entry_points={'console_scripts': ['turmeric = turmeric.__main__:_cli',],}
)
