#!/usr/bin/env python3
# -*-coding: utf-8-*-

"""Tools"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

# tools: *.py

# pylint: disable=C0302

import collections
import os
import shutil
import validate
import configobj
import numpy
import six


def cobj_check(settings, exception=None, copy=False):
    """Check for errors in config file"""

    if not exception:
        exception = Exception

    validator = validate.Validator()

    def numpy_array(val):
        """Define float list"""
        float_list = validator.functions["float_list"](val)
        return numpy.array(float_list)
    validator.functions["numpy_array"] = numpy_array

    results = settings.validate(validator, copy=copy, preserve_errors=True)
    if results is not True:
        output = "{0}: \n".format(
            settings.filename if settings.filename is not None else
            "configobj")
        for (section_list, key, error) in configobj.flatten_errors(
                settings, results):
            if key is not None:
                val = settings
                for section in section_list:
                    val = val[section]
                val = val[key] if key in val else "<EMPTY>"
                output += "   [{sections}], {key}='{val}' ({error})\n".format(
                    sections=', '.join(section_list),
                    key=key,
                    val=val,
                    error=error)
            else:
                output += "Missing section: {0}\n".format(
                    ", ".join(section_list))
        raise exception(output)


def flatten(list_of_lists):
    """Return a flattened list"""

    for elem in list_of_lists:
        if (isinstance(elem, collections.Iterable) and
                not isinstance(elem, six.string_types)):
            for sub in flatten(elem):
                yield sub
        else:
            yield elem


class Cache(object):
    """Class which save output when called"""
    # (too few public methods) pylint: disable=R0903

    def __init__(self):
        self.output = None

    def __call__(self, output):
        self.output = output
        return output


def create_dir(fname, remove=False, is_dir=False, is_file=False):
    """If the directory for fname does not exists, create it"""

    if not isinstance(fname, six.string_types):
        print("cannot create_dir for {0}".format(fname))
        return

    dirname = os.path.dirname(fname)
    if is_file:
        dirname = dirname
    elif is_dir:
        dirname = fname
    elif os.path.splitext(fname)[1] == "":
        dirname = fname

    if os.path.exists(fname) and remove:
        if os.path.islink(fname) or os.path.isfile(fname):
            os.remove(fname)
        else:
            shutil.rmtree(fname)
    if dirname != "" and not os.path.exists(dirname):
        os.makedirs(dirname)
