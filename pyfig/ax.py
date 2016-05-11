#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2016 Sander van Noort
# Licensed under GPLv3 (see LICENSE.txt)

"""Extra ax functions, including color/style"""

from __future__ import (division, unicode_literals, absolute_import,
                        print_function)

import collections
import re
import sys  # pylint: disable=W0611
import logging
import numbers

import numpy
import matplotlib.figure
import six

from .exceptions import PyfigError
from . import tools

MARKERSIZE = {
    "+": 2,
    "1": 2,
    "s": 1,
    "^": 1.5,
    "<": 1.5,
    "o": 1.5,
    "x": 1.5,
    "D": 1,
    ">": 1.5,
    "*": 2,
    "": 1}
logger = logging.getLogger(__name__)


class Axes(matplotlib.axes.Axes):
    """Axes with some extra functions"""

    def __init__(self, fig, *args, **kwargs):
        self.fig = fig
        if "row" in kwargs and "col" in kwargs:
            self.row, self.col = self.fig.get_row_col(
                kwargs.pop("row"), kwargs.pop("col"))
            args = (self.get_axpos(),)
        elif "ax1" in kwargs:
            ax1 = kwargs.pop("ax1")
            self.row = ax1.row
            self.col = ax1.col
            args = (self.get_axpos(),)
            # args = (ax1.get_axpos(),)
            ax1.parent = self
        else:
            self.row = None
            self.col = None
        self.horizontal = False
        self.parent = None
        self.ylim_manual = None
        self.xlim_manual = None
        matplotlib.axes.Axes.__init__(self, fig, *args, **kwargs)

        self.min_row, self.max_row = (
            self.row if isinstance(self.row, tuple) else
            (self.row, self.row))
        self.min_col, self.max_col = (
            self.col if isinstance(self.col, tuple) else
            (self.col, self.col))

        self.ncol = 1
        self.loc = "upper right"
        self.xaxis.tick_bottom()

    def plot(self, *args, **kwargs):
        return self._plot1("plot", *args, **kwargs)

    def axvspan(self, *args, **kwargs):
        return self._plot2("axvspan", *args, **kwargs)

    def fill(self, *args, **kwargs):
        return self._plot1("fill", *args, **kwargs)

    def axhline(self, *args, **kwargs):
        """ax.axhline function"""
        label, leg_place = self._get_label(kwargs)
        self._update_mix(kwargs, label, leg_place)
        self._update_color(kwargs)
        result = self.switch_horizontal(
            matplotlib.axes.Axes.axvline,
            matplotlib.axes.Axes.axhline,
            *args, **kwargs)
        if label:
            self.fig.add_line(result, label, leg_place)
        return result

    def axvline(self, *args, **kwargs):
        """ax.axvline function"""
        label, leg_place = self._get_label(kwargs)
        self._update_mix(kwargs, label, leg_place)
        self._update_color(kwargs)
        result = self.switch_horizontal(
            matplotlib.axes.Axes.axhline,
            matplotlib.axes.Axes.axvline,
            *args, **kwargs)
        if label:
            self.fig.add_line(result, label, leg_place)
        return result

    def get_axpos(self):
        """Determine the ax position"""
        return self.fig.get_axpos(self.row, self.col)

    def _plot1(self, ax_func, *args, **kwargs):
        """ax.ax_function, result[0] in legend"""
        label, leg_place = self._get_label(kwargs)
        self._update_mix(kwargs, label, leg_place)
        self._update_color(kwargs)
        result = getattr(matplotlib.axes.Axes, ax_func)(self, *args, **kwargs)
        if label:
            self.fig.add_line(result[0], label, leg_place)
        return result

    def _plot2(self, ax_func, *args, **kwargs):
        """ax.ax_function, result in legend"""
        label, leg_place = self._get_label(kwargs)
        self._update_mix(kwargs, label, leg_place)
        self._update_color(kwargs)
        result = getattr(matplotlib.axes.Axes, ax_func)(self, *args, **kwargs)
        if label:
            self.fig.add_line(result, label, leg_place)
        return result

    def pie(self, *args, **kwargs):
        """ax.pie function"""

        if "radius" in kwargs and matplotlib.__version__ < "1.2.1":
            # older version of matplotlib do not have radius for pie
            del kwargs["radius"]
        if "colors" in kwargs and "legends" in kwargs:
            colors = []
            for color, legend in zip(kwargs["colors"], kwargs["legends"]):
                new_kwargs = {"color": color}
                self._update_mix(new_kwargs, legend, "fig")
                self._update_color(new_kwargs)
                colors.append(new_kwargs["color"])
            kwargs["colors"] = colors

        legends = kwargs.pop("legends", None)

        if "autopct" in kwargs and kwargs["autopct"] == "values":
            def autopct(pct):
                """Define the autopct function to display the total"""
                total = sum(args[0])
                val = int(round(pct * total / 100))
                return "{0}".format(val)
                # return '{p:.2f}%  ({v:d})'.format(p=pct,v=val)
            kwargs["autopct"] = autopct

        result = matplotlib.axes.Axes.pie(self, *args, **kwargs)
        if legends:
            for line, legend in zip(result[0], legends):
                self.fig.add_line(line, legend)
        return result

    def bar(self, left, height, *args, **kwargs):
        """ax.bar function"""
        label, leg_place = self._get_label(kwargs)
        self._update_mix(kwargs, label, leg_place)
        self._update_color(kwargs)
        if "hatch" in kwargs and isinstance(kwargs["hatch"], list):
            hatches = kwargs["hatch"]
            kwargs["hatch"] = ""
        else:
            hatches = None

        if self.horizontal:
            bottom = kwargs.pop("bottom", None)
            width = kwargs.pop("width", 0.8)
            self.horizontal = False
            result = matplotlib.axes.Axes.bar(
                self, left=bottom,
                height=width, width=height, bottom=left,
                orientation="horizontal", **kwargs)
            self.horizontal = True
        else:
            result = matplotlib.axes.Axes.bar(
                self, left, height, *args, **kwargs)
        if label and len(result) > 0:
            self.fig.add_line(result[0], label, leg_place)

        if hatches:
            for hatch, mybar in zip(hatches, result):
                mybar.set_hatch(hatch)
        return result

    def errorbar(self, xcoord, ycoord, *args, **kwargs):
        """ax.errorbar function"""
        label, leg_place = self._get_label(kwargs)
        self._update_mix(kwargs, label, leg_place)
        self._update_color(kwargs)

        if kwargs.get("fmt") == "none" and matplotlib.__version__ < "1.4":
            kwargs["fmt"] = None

        if self.horizontal:
            self.horizontal = False
            yerr = kwargs.pop("yerr", None)
            result = matplotlib.axes.Axes.errorbar(
                self, ycoord, xcoord, xerr=yerr, **kwargs)
            self.horizontal = True
        else:
            result = matplotlib.axes.Axes.errorbar(
                self, xcoord, ycoord, *args, **kwargs)
        if label:
            self.fig.add_line(result[0], label, leg_place)
        return result

    def text(self, x, y, text, **kwargs):
        """ax.text function"""
        text, kwargs = self.fig.latex(text, kwargs)
        label, leg_place = self._get_label(kwargs)
        self._update_mix(kwargs, label, leg_place)
        self._update_color(kwargs)
        return matplotlib.axes.Axes.text(self, x, y, text, **kwargs)

    def set_ylabel(self, text, **kwargs):
        """Add some latex tricks"""
        text, kwargs = self.fig.latex(text, kwargs)
        if self.horizontal:
            self.horizontal = False
            result = matplotlib.axes.Axes.set_xlabel(
                self.parent if self.parent is not None else self,
                text, **kwargs)
            self.horizontal = True
        else:
            result = matplotlib.axes.Axes.set_ylabel(self, text, **kwargs)
        return result

    def set_xlabel(self, text, **kwargs):
        """set xlabel with latex tricks"""
        text, kwargs = self.fig.latex(text, kwargs)
        if self.horizontal:
            self.horizontal = False
            result = matplotlib.axes.Axes.set_ylabel(self, text, **kwargs)
            self.horizontal = True
        else:
            result = matplotlib.axes.Axes.set_xlabel(
                self.parent if self.parent is not None else self,
                text, **kwargs)
        return result

    @staticmethod
    def _get_label(kwargs):
        """Get the label, and remove it"""
        label = kwargs.pop("label", None)
        if label == "_nolegend_":
            label = None
        leg_place = kwargs.pop("leg_place", "fig")
        return label, leg_place

    def _update_color(self, kwargs):
        """Update colors and markersize"""

        for elem in (key for key in list(kwargs.keys())
                     if key.endswith("color")):
            if isinstance(kwargs[elem], list):
                for i, item in enumerate(kwargs[elem]):
                    for key, value in self.parse_color(item).items():
                        if elem[:-5] == "" or key == "color":
                            kwargs[elem[:-5] + key][i] = value
            else:
                for key, value in self.parse_color(kwargs[elem]).items():
                    if elem[:-5] == "" or key == "color":
                        kwargs[elem[:-5] + key] = value

        if "markersize" in kwargs and "marker" in kwargs:
            if kwargs["marker"] in MARKERSIZE:
                kwargs["markersize"] *= MARKERSIZE[kwargs["marker"]]
            else:
                logger.error("No markersize correction for %s",
                             repr(kwargs["marker"]))

    def set_open(self):
        """Set the ax to not have upper and right frame"""
        self.spines["top"].set_color("none")
        self.spines["right"].set_color("none")
        self.yaxis.set_ticks_position("left")

    def set_ylim(self, *args, **kwargs):
        """Set the xlimits (taking care of horizontal)"""
        if "auto" not in kwargs:
            self.ylim_manual = args
        return self.switch_horizontal(
            matplotlib.axes.Axes.set_xlim,
            matplotlib.axes.Axes.set_ylim,
            *args, **kwargs)

    def get_ylim(self, *args, **kwargs):
        """Set the xlimits (taking care of horizontal)"""
        return self.switch_horizontal(
            matplotlib.axes.Axes.get_xlim,
            matplotlib.axes.Axes.get_ylim,
            *args, **kwargs)

    def get_xlabel(self, *args, **kwargs):
        """get xlabel"""
        return self.switch_horizontal(
            matplotlib.axes.Axes.get_ylabel,
            matplotlib.axes.Axes.get_xlabel,
            *args, **kwargs)

    def get_ylabel(self, *args, **kwargs):
        """set ylabel"""
        return self.switch_horizontal(
            matplotlib.axes.Axes.get_xlabel,
            matplotlib.axes.Axes.get_ylabel,
            *args, **kwargs)

    def set_xticks(self, *args, **kwargs):
        """set xticks"""
        return self.switch_horizontal(
            matplotlib.axes.Axes.set_yticks,
            matplotlib.axes.Axes.set_xticks,
            *args, **kwargs)

    def set_yticks(self, *args, **kwargs):
        """set yticks"""
        return self.switch_horizontal(
            matplotlib.axes.Axes.set_xticks,
            matplotlib.axes.Axes.set_yticks,
            *args, **kwargs)

    def set_xticklabels(self, labels, **kwargs):
        """set xticklabels"""
        labels, kwargs = self.fig.latex(labels, kwargs)
        if self.horizontal:
            self.horizontal = False
            result = matplotlib.axes.Axes.set_yticklabels(
                self, labels, **kwargs)
            self.horizontal = True
        else:
            result = matplotlib.axes.Axes.set_xticklabels(
                self, labels, **kwargs)
        return result

    def set_yticklabels(self, labels, **kwargs):
        """set yticklabels"""
        labels, kwargs = self.fig.latex(labels, kwargs)
        if self.horizontal:
            self.horizontal = False
            result = matplotlib.axes.Axes.set_xticklabels(
                self, labels, **kwargs)
            self.horizontal = True
        else:
            result = matplotlib.axes.Axes.set_yticklabels(
                self, labels, **kwargs)
        return result

    def get_xticks(self, *args, **kwargs):
        """get xticks"""
        return self.switch_horizontal(
            matplotlib.axes.Axes.get_yticks,
            matplotlib.axes.Axes.get_xticks,
            *args, **kwargs)

    def get_yticks(self, *args, **kwargs):
        """get yticks"""
        return self.switch_horizontal(
            matplotlib.axes.Axes.get_xticks,
            matplotlib.axes.Axes.get_yticks,
            *args, **kwargs)

    def get_xticklines(self, *args, **kwargs):
        """get xticklines"""
        return self.switch_horizontal(
            matplotlib.axes.Axes.get_yticklines,
            matplotlib.axes.Axes.get_xticklines,
            *args, **kwargs)

    def get_yticklines(self, *args, **kwargs):
        """set yticklabels"""
        return self.switch_horizontal(
            matplotlib.axes.Axes.get_xticklines,
            matplotlib.axes.Axes.get_yticklines,
            *args, **kwargs)

    def get_xticklabels(self, *args, **kwargs):
        """get xticklabels"""
        return self.switch_horizontal(
            matplotlib.axes.Axes.get_yticklabels,
            matplotlib.axes.Axes.get_xticklabels,
            *args, **kwargs)

    def get_yticklabels(self, *args, **kwargs):
        """set yticklabels"""
        return self.switch_horizontal(
            matplotlib.axes.Axes.get_xticklabels,
            matplotlib.axes.Axes.get_yticklabels,
            *args, **kwargs)

    def switch_horizontal(self, func_horizontal, func, *args, **kwargs):
        """Run function based on wheter horizontal is set"""
        if self.horizontal:
            self.horizontal = False
            result = func_horizontal(self, *args, **kwargs)
            self.horizontal = True
        else:
            result = func(self, *args, **kwargs)
        return result

    def set_xlim(self, *args, **kwargs):
        """Set the xlimits (taking care of horizontal)"""
        if "auto" not in kwargs:
            self.xlim_manual = args
        return self.switch_horizontal(
            matplotlib.axes.Axes.set_ylim,
            matplotlib.axes.Axes.set_xlim,
            *args, **kwargs)

    def get_xlim(self, *args, **kwargs):
        """Set the xlimits (taking care of horizontal)"""
        return self.switch_horizontal(
            matplotlib.axes.Axes.get_ylim,
            matplotlib.axes.Axes.get_xlim,
            *args, **kwargs)

    def set_xstyle(self, style):
        """Set the style of x-axis for the date"""

        if style == "month":
            self.xaxis.set_major_formatter(
                matplotlib.dates.DateFormatter("%b"))
            self.xaxis.set_major_locator(
                matplotlib.dates.MonthLocator())
        elif style in ("month2", "month3", "month4"):
            self.xaxis.set_major_formatter(
                matplotlib.dates.DateFormatter("%b"))
            self.xaxis.set_major_locator(
                matplotlib.dates.MonthLocator(interval=int(style[-1])))
        elif style == "year":
            self.xaxis.set_major_formatter(
                matplotlib.dates.DateFormatter("%Y"))
            self.xaxis.set_major_locator(
                matplotlib.dates.YearLocator())
        elif style == "week":
            self.xaxis.set_major_formatter(
                matplotlib.dates.DateFormatter("%W"))
            self.xaxis.set_major_locator(
                matplotlib.dates.WeekdayLocator(
                    byweekday=matplotlib.dates.SU, interval=2))

    def barplot(self, data, labels, colors, **kwargs):
        """Bar plot"""

        options = {"city_distance": 0.2,
                   "house_distance": 0.1,
                   "padding": 0,
                   "leg_place": "fig",
                   "alpha": 1,
                   "capsize": 2}
        options.update(kwargs)

        labels = collections.defaultdict(lambda: [None], labels)

        options["house_space"] = ((1 - options["city_distance"]) /
                                  len(labels["house"]))
        options["house_width"] = ((1 - options["house_distance"]) *
                                  options["house_space"])

        for house in range(len(labels["house"])):
            yoff = numpy.zeros(len(labels["city"]))
            for floor in range(len(labels["floor"])):
                non_zeros = []
                bar_data = []
                indent = []
                for city in range(len(labels["city"])):
                    city_values = [
                        (value, 0, 0) if isinstance(value, numbers.Number) else
                        value
                        for key, value in data.items()
                        if (labels["city"][city] in key or
                            labels["city"] == [None]) and
                        (labels["house"][house] in key or
                         labels["house"] == [None]) and
                        (labels["floor"][floor] in key or
                         labels["floor"] == [None])]
                    if len(city_values) > 0:
                        bar_data.append(numpy.sum(city_values, axis=0))
                        non_zeros.append(city)
                    else:
                        bar_data.append([0, 0, 0])
                    indent.append(
                        city +
                        0.5 * (options["city_distance"] +
                               options["house_distance"] *
                               options["house_space"]) +
                        house * options["house_space"])

                if len(bar_data) == 0:
                    raise PyfigError("Empty barplot")
                bar_data = numpy.array(bar_data)
                indent = numpy.array(indent)
                label, color = self._get_barcolor(labels, colors,
                                                  house, floor)
#                 ax.plot(
#                     indent[non_zeros],
#                     bar_data[non_zeros, 0],
#                     linestyle=None,
#                     color=black)
                if isinstance(color, list) and None in color:
                    color = None
                if color is not None:
                    self.bar(
                        indent[non_zeros],
                        bar_data[non_zeros, 0],
                        width=options["house_width"],
                        color=color,
                        label=label,
                        bottom=yoff[non_zeros],
                        leg_place=options["leg_place"])
                if bar_data[:, 1:].sum() > 0:
                    self.errorbar(
                        indent[non_zeros] + 0.5 * options["house_width"],
                        bar_data[non_zeros, 0] + yoff[non_zeros],
                        yerr=bar_data[non_zeros, 1:].transpose(),
                        fmt="o" if color is None else "none",
                        ecolor="black",
                        color="black",
                        linewidth=0.6,
                        capsize=options["capsize"])
                yoff += bar_data[:, 0]

        self.set_xticks(numpy.arange(len(labels["city"])) + 0.5)
        self.set_xticklabels(["{0}".format(label).replace("__", "\n")
                              for label in labels["city"]])
        self.set_xlim(0 - options["padding"],
                      len(labels["city"]) + options["padding"])
        for tick in self.get_xticklines():
            tick.set_markersize(0)

    def _get_barcolor(self, labels, colors, house, floor):
        """Get the color of the bars"""

        if "city" in colors:
            color = colors["city"][0:len(labels["city"])]
            label = None

        elif (labels["house"][house] is not None and
              labels["floor"][floor] is not None):

            house_color = self.parse_color(colors["house"][house])
            if "hatch" in house_color:
                hatchlabel = labels["house"][house]
                hatch = house_color.pop("hatch")
                color = house_color
            else:
                label = labels["house"][house]

            floor_color = self.parse_color(colors["floor"][floor])
            if "hatch" in floor_color:
                hatchlabel = labels["floor"][floor]
                hatch = floor_color.pop("hatch")
                color = floor_color
            else:
                label = labels["floor"][floor]

            # Draw temporary bar for hatch legend
            logger.error("hatch=%s, hatchlabel=%s", hatch, hatchlabel)
#             ax.bar(indent[non_zeros],
#                 bar_data[non_zeros, 0],
#                 options["house_width"],
#                 color="white",
#                 label=hatchlabel,
#                 bottom=yoff[non_zeros],
#                 hatch=hatch,
#                 leg_place="fig2")

        elif labels["house"][house] is not None:
            color = colors["house"][house]
            label = labels["house"][house]
        elif labels["floor"][floor] is not None:
            color = colors["floor"][floor]
            label = labels["floor"][floor]

#         elif "house" in colors and house < len(colors["house"]):
#             # Empty house labels
#             color = colors["house"][house]
#         elif "floor" in colors and floor < len(colors["floor"]):
#             # Empty floor labels
#             color = colors["floor"][floor]
        else:
            sys.exit("No house/floor available")

#         if label and isinstance(label, six.string_types):
#             label = label.replace("__", "\n")

        if isinstance(color, list) and color[0] == "mix":
            color = "mix"

        return label, color

    @staticmethod
    def parse_color(color):
        """Parse the color, return a dict with
            color, hatch (optional), and alpha (optional)"""

        cache = tools.Cache()
        result = {}

        if (isinstance(color, six.string_types) and
                cache(re.search(r"-*h\((.*?)\)", color))):
            color = color.replace(cache.output.group(), "")
            result["hatch"] = cache.output.group(1)
        if (isinstance(color, six.string_types) and
                cache(re.search(r"-*a\((.*?)\)", color))):
            color = color.replace(cache.output.group(), "")
            result["alpha"] = float(cache.output.group(1))
        if (isinstance(color, six.string_types) and
                cache(re.search(r"-*s\((.*?)\)", color))):
            color = color.replace(cache.output.group(), "")
            result["linestyle"] = cache.output.group(1)
        if (isinstance(color, six.string_types) and
                cache(re.search(r"-*m\((.*?)\)", color))):
            color = color.replace(cache.output.group(), "")
            result["marker"] = cache.output.group(1)

        if color == "":
            color = "white"

        if (isinstance(color, six.string_types) and
                cache(re.search(r"hex\((.*)\)", color))):
            color = cache.output.group(1)
            color = (int(color[0:2], 16) / 255,
                     int(color[2:4], 16) / 255,
                     int(color[4:6], 16) / 255)

        if isinstance(color, six.string_types):
            all_numbers = re.findall(r"[\.\d]+", color)
            if len(all_numbers) == 3:
                color = [float(number) for number in all_numbers]
                if max(color) > 1:
                    color = [number / 255 for number in color]

        result["color"] = color
        return result

    def __lt__(self, other):
        if isinstance(other, six.string_types):
            result = False
        else:
            result = (
                self.min_row < other.min_row or
                self.min_row == other.min_row and self.min_col < other.min_col)
        if self.fig.settings["abc_reverse"]:
            result = not result
        return result

    def __gt__(self, other):
        return not self.__lt__(other)

    def _update_mix(self, kwargs, label, leg_place):
        """Update the elements with color/line/.. = mix"""

        cache = tools.Cache()

        if leg_place not in self.fig.repo:
            self.fig.repo[leg_place] = list(self.fig.repo["all"])
        style = self.fig.style[leg_place]
        repo = self.fig.repo[leg_place]

        for subcolor in (key for key in kwargs.keys()
                         if key.endswith("color")):
            if kwargs[subcolor] == "mix":
                elemlabel = label
            elif (isinstance(kwargs[subcolor], six.string_types) and
                  cache(re.search(r"mix\((.*)\)", kwargs[subcolor]))):
                elemlabel = cache.output.group(1)
            else:
                continue

            if elemlabel in style:
                kwargs[subcolor] = style[elemlabel]
                # TODO: remove possible same color still in style
#                 if style[elemlabel] in repo:
#                     repo.remove(style[elemlabel])
            else:
                kwargs[subcolor] = repo[0] if len(repo) == 1 else repo.pop(0)
                style[elemlabel] = kwargs[subcolor]
