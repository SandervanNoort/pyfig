#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2016 Sander van Noort
# Licensed under GPLv3 (see LICENSE.txt)

"""Init the PyFig class"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import os

ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_DIR = os.path.join(ROOT, "config")
