#!usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2016 Sander van Noort
# Licensed under GPLv3 (see LICENSE.txt)

"""Pyfig installation"""


from setuptools import setup

setup(
    name="pyfig",
    packages=["pyfig"],
    version="201605.1",
    author="Sander van Noort",
    author_email="epispread@gmail.com",
    url = 'https://github.com/epispread/pyfig',
    download_url = 'https://github.com/epispread/pyfig/tarball/201605.1',
    keywords = ["matplotlib", "python", "plotting"],
    classifiers = [])

#     cmdclass={"build_py": build_py},
#     description="Wrapper around matplotlib to create figures",
#     license="GPL v3",
#     data_files=["config/settings.spec"])
