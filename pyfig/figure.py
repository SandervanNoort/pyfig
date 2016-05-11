#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2016 Sander van Noort
# Licensed under GPLv3 (see LICENSE.txt)

"""Figures based on ini-files"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import sys  # pylint: disable=W0611
import locale
import os
import collections
import re
import copy
import datetime
import configobj
import matplotlib.figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as canvas
from six import StringIO
import six

from .ax import Axes
from .exceptions import PyfigError
from . import config, tools


class Figure(matplotlib.figure.Figure):
    """The Figure class"""
    # (too many public) pylint: disable=R0904

    def __init__(self, settings=None, setup=True, check=False):
        if isinstance(settings, six.string_types):
            settingsfile = StringIO()
            settings = re.sub(r" *\\\n *", " ", settings)
            settingsfile.write(settings)
            settingsfile.seek(0)
            self.settings = configobj.ConfigObj(
                settingsfile,
                configspec=os.path.join(config.CONFIG_DIR, "settings.spec"))
            tools.cobj_check(self.settings, exception=PyfigError)
        elif check:
            self.settings = configobj.ConfigObj(
                settings,
                configspec=os.path.join(config.CONFIG_DIR, "settings.spec"))
            tools.cobj_check(self.settings, exception=PyfigError)
        else:
            self.settings = settings

        self.rows = []
        self.cols = []
        self.title = None
        self.repo = self._get_repo()
        self.plotlines = collections.defaultdict(list)
        self.labels = collections.defaultdict(list)
        self.style = collections.defaultdict(
            lambda: collections.defaultdict(dict))

        if setup:
            matplotlib.figure.Figure.__init__(
                self, figsize=self.settings["figsize"])
            self.setup()

    def setup(self):
        """Set up the figure"""

        canvas(self)
        self.width = self.get_figwidth() * self.get_dpi()
        self.height = self.get_figheight() * self.get_dpi()
        self._set_locale()
        matplotlib.rcParams.update(self.settings["rc"])

        margins = self.settings["margins"]
        self.cols = [[margins["figure"][3], 0, margins["ax"]]]
        for _loop in range(len(self.settings["cols"]) - 1):
            self.cols.append([margins["ax"], margins["ax_col"], margins["ax"]])
        self.cols.append([margins["ax"], 0, margins["figure"][1]])
        self.rows = [[margins["figure"][0], 0, margins["ax"]]]
        for _loop in range(len(self.settings["rows"]) - 1):
            self.rows.append([margins["ax"], margins["ax_row"], margins["ax"]])
        self.rows.append([margins["ax"], 0, margins["figure"][2]])

        if sum(self.settings["rows"]) > 1:
            self.settings["rows"] = [row / sum(self.settings["rows"])
                                     for row in self.settings["rows"]]
        if sum(self.settings["cols"]) > 1:
            self.settings["cols"] = [col / sum(self.settings["cols"])
                                     for col in self.settings["cols"]]

    def get_row_col(self, row, col):
        """Return row and col
           Raises warning if not available as row"""

        if isinstance(col, int) and col > 100:
            col = (col // 10) % 10, (col // 1) % 10
        if isinstance(row, int) and row > 100:
            row = (row // 10) % 10, (row // 1) % 10

        for row_no in [row] if isinstance(row, int) else row:
            if row_no not in range(len(self.settings["rows"])):
                raise PyfigError("row {row} added, {rows} available".format(
                    row=row, rows=len(self.settings["rows"])))
        for col_no in [col] if isinstance(col, int) else col:
            if col_no not in range(len(self.settings["cols"])):
                raise PyfigError("col {col} added, {cols} available".format(
                    col=col, cols=len(self.settings["cols"])))

        return row, col

    def add_ax(self, row=0, col=0, *args, **kwargs):
        """Add an axes"""

        ax = Axes(self, row=row, col=col, *args, **kwargs)
        self.add_axes(ax)
        return ax

    def add_ax2(self, ax1, no_axes=2, left=True):
        """Add a second ax"""
        ax2 = (Axes(self, ax1=ax1, frameon=False, sharex=ax1)
               if no_axes == 2 else
               Axes(self, ax1=ax1, frameon=False))
        self.add_axes(ax2)
        if left:
            ax1.yaxis.tick_right()
            ax2.yaxis.tick_left()
            ax1.yaxis.set_label_position('right')
            ax2.yaxis.set_label_position('left')
            for ticklabel in ax1.get_xticklabels():
                ticklabel.set_visible(False)
            for tline in ax1.get_xticklines():
                tline.set_visible(False)
        else:
            ax1.yaxis.tick_left()
            ax2.yaxis.tick_right()
            ax1.yaxis.set_label_position('left')
            ax2.yaxis.set_label_position('right')
            for ticklabel in ax2.get_xticklabels():
                ticklabel.set_visible(False)
            for tline in ax2.get_xticklines():
                tline.set_visible(False)
        return ax2

    def _update_figsize(self):
        """Update the figsize"""
        self.set_figheight(
            (self.height + sum(tools.flatten(self.rows))) /
            self.get_dpi())
        self.height = self.get_figheight() * self.get_dpi()
        self.set_figwidth(
            self.get_figwidth() +
            sum(tools.flatten(self.cols)) / self.get_dpi())
        self.width = self.get_figwidth() * self.get_dpi()
        for ax in self.get_new_axes():
            ax.set_position(ax.get_axpos())

    def save(self, figname=None, **kwargs):
        """Save the figure"""

        self._save_extras()
        if self.settings["title"] != "":
            self.title = self.text(
                (self.settings["margins"]["figure"][3] / self.width
                 if self.settings["title_loc"] == "left" else 0.5),
                1 - self.settings["margins"]["figure"][0] / self.height,
                self.settings["title"].replace("__", "\n"),
                weight="bold",
                fontsize=13,
                verticalalignment="top",
                horizontalalignment=(
                    "left" if self.settings["title_loc"] == "left" else
                    "center")
                )

        self._save_legend()
        self._temp_save()

        self._update_margins()
        self._update_margins_legend()
        self._redraw_legend()

        if self.settings["resize"]:
            self._update_figsize()
        if self.settings["abc_labels"]:
            self._abc_labels()

        if self.settings["date"] != "":
            match = re.match(r"now\((.*)\)", self.settings["date"])
            self.text(
                0.99,
                0.01,
                datetime.datetime.now().strftime(match.group(1)) if match else
                self.settings["date"],
                fontsize=8, va="bottom", ha="right",
                family="Arial", style="italic")

        if self.settings["logo"] != "":
            img = matplotlib.image.imread(self.settings["logo"])
            inset = img.shape[1] / self.width + 0.01
            self.figimage(img, 1, 1)
        else:
            inset = 1 / self.width
        if self.settings["url"] != "":
            self.text(inset, 1 / self.height, self.settings["url"],
                      fontsize=8, va="bottom", ha="left",
                      family="Arial", style="italic")

        for ax in self.get_new_axes():
            if ax.yaxis.get_label_position() == "right":
                ax.yaxis.label.set_rotation(270)
                # this is connected to va in axes_align
                ax.yaxis.label.set_va("bottom")

        if self.settings["axes_align"]:
            self._temp_save()
            self._axes_align()

        self._single_labels()
        self._fit_axlabels()
        self._temp_save()
        self._check_ticks()

        self.savefig(figname, **kwargs)

    def _fit_axlabels(self):
        """Update ymargins such that ax.labels fit"""
        for ax in self.get_new_axes():
            if not hasattr(ax, "labels"):
                continue
            ax_ymin, ax_ymax = (ax.get_window_extent().ymin,
                                ax.get_window_extent().ymax)
            data_ymax = ax.dataLim.ymax
            ymin, ymax = ax.get_ylim()
            if (ax.ylim_manual is not None and
                    len(ax.ylim_manual) > 1 and
                    ax.ylim_manual[1] is not None):
                continue
            for label in ax.labels:
                label_perc = ((ax_ymax - label.get_window_extent().ymin) /
                              (ax_ymax - ax_ymin)) * 1.2
                cur_perc = (ymax - data_ymax) / (ymax - ymin)
                if cur_perc > label_perc:
                    continue
                if ax.horizontal:
                    ax.set_xlim(None,
                                ymin + (data_ymax - ymin) / (1 - label_perc))
                else:
                    ax.set_ylim(None,
                                ymin + (data_ymax - ymin) / (1 - label_perc))
                    ax.set_yticks(ax.get_yticks())

    def _get_repo(self):
        """Get the repo for the colors etc"""

        cache = tools.Cache()
        repo = collections.defaultdict(dict)
        for key in self.settings.keys():
            if cache(re.match("(.*)_colors", key)):
                repo[cache.output.group(1)] = list(self.settings[key])
        repo["all"] = list(self.settings["colors"])
        return repo

    def get_axpos(self, row, col):
        """Determine the ax position"""

        min_row, max_row = (row if isinstance(row, tuple) else
                            (row, row))
        axes_h = self.height - sum(tools.flatten(self.rows))
        ax_h = (sum(self.settings["rows"][min_row:max_row + 1]) * axes_h +
                sum(tools.flatten(
                    self.rows[min_row + 1:max_row + 1])))
        ax_y = (sum(tools.flatten(self.rows[max_row + 1:])) +
                sum(self.settings["rows"][max_row + 1:]) * axes_h)

        min_col, max_col = (col if isinstance(col, tuple) else
                            (col, col))
        axes_w = self.width - sum(tools.flatten(self.cols))
        ax_w = (sum(self.settings["cols"][min_col:max_col + 1]) * axes_w +
                sum(tools.flatten(
                    self.cols[min_col + 1:max_col + 1])))
        ax_x = (sum(tools.flatten(self.cols[:min_col + 1])) +
                sum(self.settings["cols"][:min_col]) * axes_w)

        return [ax_x / self.width, ax_y / self.height,
                ax_w / self.width, ax_h / self.height]

    def _single_labels(self):
        """Put the single label back"""

        for ax in self.get_new_axes():
            if hasattr(ax, "single_xlabel"):
                xmin, ymin, width, height = self.get_axpos(
                    len(self.settings["rows"]) - 1,
                    (0, len(self.settings["cols"]) - 1))
                ymin = (self.rows[-1][2] / self.height)
                # label_pos = ax.xaxis.get_label().get_window_extent()
                # ax_pos = ax.get_window_extent()
                # ymin = (ax_pos.ymin + label_pos.ymin) / self.height
                self.text(xmin + width / 2, ymin,
                          ax.single_xlabel,
                          va="bottom",
                          ha="center",
                          color=ax.xaxis.get_label().get_color(),
                          fontsize=ax.xaxis.get_label().get_fontsize())
                ax.xaxis.set_label_text("")

            if (hasattr(ax, "single_ylabel") and
                    ax.yaxis.get_label_position() == "left"):
                xmin, ymin, width, height = self.get_axpos(
                    (0, len(self.settings["rows"]) - 1), 0)
                xval = self.cols[0][0] / self.width
                self.text(
                    xval, ymin + height / 2,
                    ax.single_ylabel,
                    va="center",
                    ha="left",
                    color=ax.yaxis.get_label().get_color(),
                    fontsize=ax.yaxis.get_label().get_fontsize(),
                    rotation=ax.yaxis.get_label().get_rotation())
                ax.yaxis.set_label_text("")

            if (hasattr(ax, "single_ylabel") and
                    ax.yaxis.get_label_position() == "right"):
                xmin, ymin, width, height = self.get_axpos(
                    (0, len(self.settings["rows"]) - 1),
                    len(self.settings["cols"]) - 1)
                xval = 1 - (self.cols[-1][2] / self.width)
                self.text(
                    xval, ymin + height / 2,
                    ax.single_ylabel,
                    va="center",
                    ha="right",
                    color=ax.yaxis.get_label().get_color(),
                    fontsize=ax.yaxis.get_label().get_fontsize(),
                    rotation=ax.yaxis.get_label().get_rotation())
                ax.yaxis.set_label_text("")

    def savefig(self, figname=None, dpi=None, **kwargs):
        """Save the final fig to disk"""
        if figname is None:
            figname = self.settings["figname"]

        if dpi is None:
            dpi = self.settings["dpi"]
        tools.create_dir(figname)
        if "transparent" in kwargs:
            matplotlib.figure.Figure.savefig(
                self, figname, dpi=dpi, **kwargs)
        else:
            matplotlib.figure.Figure.savefig(
                self, figname, facecolor=self.settings["facecolor"],
                dpi=dpi, **kwargs)

    def _temp_save(self):
        """Save a temporary figure"""
        figname = "/tmp/{0}.png".format(os.getpid())
        self.savefig(figname, dpi=80)
        os.remove(figname)

    def _set_locale(self):
        """Set the language of the plot"""

        if self.settings["lang"] == "pt":
            locale.setlocale(locale.LC_ALL, str("pt_PT.UTF-8"))
        elif self.settings["lang"] == "nl":
            locale.setlocale(locale.LC_ALL, str("nl_NL.UTF-8"))
        elif self.settings["lang"] == "en":
            locale.setlocale(locale.LC_ALL, str("C"))  # en_US.UTF-8"))

    def _save_legend(self):
        """Print the final legend"""

        for ax in sorted(self.plotlines.keys()):
            lines = self.plotlines[ax]
            labels = self.labels[ax]
            if len(lines) == 0:
                continue

            if isinstance(ax, matplotlib.axes.Axes):
                ax.legend(lines, labels, loc=ax.loc, ncol=ax.ncol)
            elif isinstance(ax, six.string_types):
                legend = self.legend(
                    lines, labels, loc=(0, 0),
                    ncol=(len(lines) if self.settings["ncol"] == 0 else
                          self.settings["ncol"]))
                legend.lines = lines
                legend.labels = labels
                legend.draw_frame(1)
                legend.ncol = self.settings["ncol"]
                self._set_legend_rowcol(legend, ax)
            else:
                raise PyfigError("Unknown ax for lines: {0}".format(ax))

    def _set_legend_rowcol(self, legend, ax):
        """Set the row and col for the legend"""

        legend.row, legend.col = None, None
        if re.search(r"^row(\d+).*", ax):
            legend.row = int(re.search(r"^row(\d+).*", ax).group(1))
        elif re.search(r"^col(\d+).*", ax):
            legend.col = int(re.search(r"^col(\d+).*", ax).group(1))
        elif self.settings["legend_loc"] == "outer right":
            legend.col = len(self.settings["cols"]) - 1
        elif self.settings["legend_loc"] == "outer top":
            legend.row = 0
        elif self.settings["legend_loc"] == "outer left":
            legend.col = 0
        elif self.settings["legend_loc"] == "outer bottom":
            legend.row = len(self.settings["rows"]) - 1
        else:
            raise PyfigError("Unknown legend row,col for ax {0}".format(ax))

    def _set_legend_size(self, legend):
        """Set the width of the legend, such that it fits"""

        legend.width = legend.get_frame().get_width()
        legend.height = legend.get_frame().get_height()

        legend_space = (self.width - sum(self.cols[0]) -
                        sum(self.cols[-1]))

        ncol = len(legend.lines)
        # legend_rows = 1
        while legend.width > legend_space and ncol > 1:
                # legend_rows < len(legend.lines)):
            # legend_rows += 1
            prev_leg = self.legends.pop()  # pylint: disable=W0612
            # W0612: unused variable prev_leg
            prev_leg = None

            ncol -= 1
            # ncol = int(math.ceil(len(legend.lines) / legend_rows))
            legend_orig = legend
            legend_orig.deleted = True
            legend = self.legend(
                legend_orig.lines, legend_orig.labels, loc=(0, 0),
                ncol=ncol)
            legend.lines = legend_orig.lines
            legend.labels = legend_orig.labels
            legend.draw_frame(1)
            legend.ncol = ncol
            legend.row = legend_orig.row
            legend.col = legend_orig.col
            self._temp_save()
            legend.width = legend.get_frame().get_width()
            legend.height = legend.get_frame().get_height()
        return legend

    def _update_margins(self):
        """Update all margins (for xlabels, title, legends etc.)"""

        rows = copy.deepcopy(self.rows)
        cols = copy.deepcopy(self.cols)

        if self.title:
            pos = self.title.get_window_extent()
            # latex with supscript $^$ creates vertical margin...
            self.rows[0][0] = max(
                self.settings["margins"]["title_row"] +
                self.height - pos.ymin,
                self.settings["margins"]["title"])

        if self.settings["date"] != "" or self.settings["url"] != "":
            self.rows[-1][2] = max(self.rows[-1][2], 15)

        for ax in self.get_new_axes():
            pos = ax.get_window_extent()
            labels = [label for label in ax.get_xticklabels() +
                      ax.get_yticklabels() +
                      [ax.yaxis.get_label(), ax.xaxis.get_label()] +
                      ax.texts
                      if label.get_visible() and
                      label.get_text() != ""]

            if len(labels) == 0:
                continue

            ymin = min([label.get_window_extent().ymin
                        for label in labels])
            self.rows[ax.max_row + 1][0] = max(
                self.rows[ax.max_row + 1][0],
                pos.ymin - ymin)

            xmin = min([label.get_window_extent().xmin
                        for label in labels]) - 2
            self.cols[ax.min_col][2] = max(
                self.cols[ax.min_col][2],
                pos.xmin - xmin)

            xmax = max([label.get_window_extent().xmax
                        for label in labels])
            self.cols[ax.max_col + 1][0] = max(
                self.cols[ax.max_col + 1][0],
                xmax - pos.xmax)

            ymax = max([label.get_window_extent().ymax
                        for label in labels])
            self.rows[ax.min_row][2] = max(
                self.rows[ax.min_row][2],
                ymax - pos.ymax)

        for ax in self.get_new_axes():
            ax.set_position(ax.get_axpos())

        # some functions such as ax.pie, redraw labels if there is allocated
        # more space
        if (not self.settings["resize"] and
                (round(sum(tools.flatten(self.cols)), 1) !=
                 round(sum(tools.flatten(cols)), 1) or
                 round(sum(tools.flatten(self.rows)), 1) !=
                 round(sum(tools.flatten(rows)), 1))):
            self._temp_save()
            self._update_margins()

    def _update_margins_legend(self):
        """Update the row and col margins for the legend"""

        margins = self.settings["margins"]
        for legend in self.legends:
            legend = self._set_legend_size(legend)
            if legend.row is not None:
                self.rows[legend.row][1] += \
                    legend.height + 2 * margins["legend_row"]
            if legend.col is not None:
                self.cols[legend.col + 1][1] += \
                    legend.width + 2 * margins["legend_col"]
        for ax in self.get_new_axes():
            # legend = self._set_legend_size(legend)
            ax.set_position(ax.get_axpos())

    def _redraw_legend(self):
        """Redraw the legend"""
        rows = {}
        margins = self.settings["margins"]

        for legend in self.legends:
            if hasattr(legend, "deleted"):
                continue
            if legend.row is not None:
                row = legend.row
                col = (0, len(self.settings["cols"]) - 1)
            elif legend.col is not None:
                col = legend.col
                row = (0, len(self.settings["rows"]) - 1)
            else:
                raise PyfigError("Unknown col/row for legend")
            pos = self.get_axpos(row, col)
            if isinstance(row, int):
                if row not in rows:
                    yval = (self.height * (pos[1] + pos[3]) +
                            self.rows[row][2] +
                            margins["legend_row"])
                    rows[row] = yval + margins["legend_row"] + legend.height
                else:
                    yval = rows[row] + margins["legend_row"]
                    rows[row] += margins["legend_row"] + legend.height
                xval = self.width * (pos[0] + pos[2]) - legend.width
            else:
                yval = self.height * (pos[1] + pos[3]) - legend.height
                xval = (self.width * (pos[0] + pos[2]) +
                        self.cols[col + 1][0] +
                        margins["legend_col"])

            # (access to protected member) pylint: disable=W0212
            legend._loc = (xval / self.width, yval / self.height)

    def _bottom_labels(self, xticks):
        """Set the bottom label to be empty when not the last"""
        labels = collections.defaultdict(list)
        for ax in self.get_new_axes():
            for col in range(ax.min_col, ax.max_col + 1):
                xlabel = ax.xaxis.get_label().get_text()
                labels[(xlabel, col)].append(ax.max_row)

        for ax in self.get_new_axes():
            xlabel = ax.xaxis.get_label().get_text()
            for col in range(ax.min_col, ax.max_col + 1):
                if ax.max_row < max(labels[(xlabel, col)]):
                    ax.xaxis.set_label_text("")
                    if xticks:
                        ax.xaxis.set_ticklabels([""] *
                                                len(ax.xaxis.get_ticklocs()))

    def _single_xlabel(self):
        """A single xlabel for axes with same label next to eachother"""

        labels = collections.defaultdict(list)
        for ax in self.get_new_axes():
            xlabel = ax.xaxis.get_label().get_text()
            for col in range(ax.min_col, ax.max_col + 1):
                labels[(xlabel, ax.max_row)].append(col)

        for ax in self.get_new_axes():
            xlabel = ax.xaxis.get_label().get_text()
            if (xlabel, ax.max_row) not in labels:
                ax.xaxis.set_label_text("")
            elif len(labels[(xlabel, ax.max_row)]) != 1:
                ax.xaxis.set_label_text(xlabel[0:10])
                ax.single_xlabel = xlabel
                del labels[(xlabel, ax.max_row)]

    def _left_labels(self, yticks):
        """Set the bottom label to be empty when not the last"""
        labels = collections.defaultdict(list)
        for ax in self.get_new_axes():
            for row in range(ax.min_row, ax.max_row + 1):
                pos = ax.yaxis.get_label_position()
                labels[(ax.get_ylabel(), row, pos)].append(ax.max_col)

        for ax in self.get_new_axes():
            ylabel = ax.get_ylabel()
            pos = ax.yaxis.get_label_position()
            for row in range(ax.min_row, ax.max_row + 1):
                if (pos == "right" and
                        ax.max_col < max(labels[(ylabel, row, pos)])):
                    ax.set_ylabel("")
                    if yticks:
                        ax.set_yticklabels([""] * len(ax.get_yticks()))
                elif (pos == "left" and
                      ax.min_col > min(labels[(ylabel, row, pos)])):
                    ax.yaxis.set_label_text("")
                    if yticks:
                        ax.yaxis.set_ticklabels(
                            [""] * len(ax.yaxis.get_ticklocs()))

    def _single_ylabel(self):
        """A single xlabel for axes with same label next to eachother"""

        labels = collections.defaultdict(list)
        for ax in self.get_new_axes():
            pos = ax.yaxis.get_label_position()
            ylabel = ax.yaxis.get_label().get_text()
            for row in range(ax.min_row, ax.max_row + 1):
                labels[(ylabel, ax.min_col, pos)].append(row)

        for ax in self.get_new_axes():
            pos = ax.yaxis.get_label_position()
            ylabel = ax.yaxis.get_label().get_text()
            if (ylabel, ax.min_col, pos) not in labels:
                ax.yaxis.set_label_text("")
            elif len(labels[(ylabel, ax.min_col, pos)]) != 1:
                ax.yaxis.set_label_text(ylabel[0:10])
                ax.single_ylabel = ylabel
                del labels[(ylabel, ax.min_col, pos)]

    def ax_labels(self):
        """Put axes titles"""

        for ax in self.get_new_axes():
            ax.labels = []
            # ax_width, ax_height = ax.get_position().bounds[2:]
            if hasattr(ax, "label"):
                label = ax.text(
                    8 / (ax.get_axpos()[2] * self.width),
                    1 - 5 / (ax.get_axpos()[3] * self.height),
                    ax.label,
                    va="top", ha="left",
                    transform=ax.transAxes,
                    style=self.settings["ax_label_style"],
                    fontsize=self.settings["margins"]["ax_label_size"])
                ax.labels.append(label)
            if hasattr(ax, "topright"):
                label = ax.text(
                    0.99, 0.97,
                    # 1 - hmargin, 1 - vmargin,
                    ax.topright,
                    va="top", ha="right",
                    transform=ax.transAxes,
                    style=self.settings["ax_label_style"],
                    fontsize=self.settings["margins"]["ax_label_size"])
                ax.labels.append(label)

    def _abc_labels(self):
        """Set the A), B) and C) labels"""
        prev_row, prev_col = None, None
        label = "A"

        for ax in sorted(list(self.get_new_axes())):
            if not ax.axison:
                continue
            if ax.yaxis.get_label_position() == "right":
                continue
            if (ax.min_row, ax.min_col) != (prev_row, prev_col):
                pos = ax.get_position().bounds
                left_margin = (- self.settings["margins"]["abc"] /
                               (pos[2] * self.width))
                ax.abc_label = ax.text(left_margin, 1, label,
                                       transform=ax.transAxes,
                                       weight="bold",
                                       va=self.settings["abc_align"],
                                       ha="right",
                                       fontsize=14)

                label = chr(ord(label) + 1)
                prev_row, prev_col = ax.min_row, ax.min_col

    def get_new_axes(self):
        for ax in self.get_axes():
            if hasattr(ax, "horizontal"):
                yield ax

    def _set_ticksize(self):
        """reduce ticklabel size"""
        for ax in self.get_new_axes():
            if ax.horizontal or len(ax.get_yticks()) == 0:
                continue

            if max(ax.get_yticks()) > 10000:
                # ax.tick_params(axis="y", labelsize=6)
                for tick in ax.yaxis.get_major_ticks():
                    tick.label.set_fontsize(tick.label.get_fontsize() - 2)
            elif max(ax.get_yticks()) > 1000:
                # ax.tick_params(axis="y", labelsize=7)
                for tick in ax.yaxis.get_major_ticks():
                    tick.label.set_fontsize(tick.label.get_fontsize() - 1)

    def _save_extras(self):
        """Some extra things to do before saving"""

        if self.settings["ax_open"]:
            for ax in self.get_new_axes():
                ax.set_open()
        if self.settings["bottom_labels"]:
            self._bottom_labels(self.settings["bottom_xticks"])
        if self.settings["single_xlabel"]:
            self._single_xlabel()
        if self.settings["left_labels"]:
            self._left_labels(self.settings["left_yticks"])
        if self.settings["single_ylabel"]:
            self._single_ylabel()
        if self.settings["ax_labels"]:
            self.ax_labels()
        self._set_ticksize()

    def _check_ticks(self):
        """Remove ticks which overlap"""

        # sorted ?
        for ax in self.get_new_axes():
            if ax.horizontal:
                continue

            ymax = ax.get_ylim()[1]
            yticklabels = ax.get_yticklabels()
            if len(yticklabels) == 0:
                continue

            if hasattr(ax, "abc_label"):
                abc_box = ax.abc_label.get_window_extent()
                ylabels = []
                yticks = []
                for ytick, ylabel in zip(ax.get_yticks(), yticklabels):
                    if ytick > ymax:
                        continue
                    ylabel_box = ylabel.get_window_extent()
                    if ylabel_box.ymax + 2 < abc_box.ymin:
                        ylabels.append(ylabel.get_text())
                        yticks.append(ytick)
                ax.set_yticklabels(ylabels)
                ax.set_yticks(yticks)

    @staticmethod
    def __axes_align_col(axes, left=True):
        """Align the ylabel from selected axes
            left whether the label is on the left side"""

        if len(axes) < 1:
            return
        boxes = [ax.yaxis.get_label().get_window_extent()
                 for ax in axes
                 if ax.yaxis.get_label().get_text() != ""]
        if len(boxes) == 0:
            return
        display_x = (min([box.xmax for box in boxes]) if left else
                     max([box.xmin for box in boxes]))
        for ax in axes:
            # box = ax.yaxis.get_label().get_window_extent()
            ax_we = ax.get_window_extent()

            ax_x = ((display_x - ax_we.xmin) / ax_we.width if left else
                    1 + (display_x - ax_we.xmax) / ax_we.width)
            ax_y = ax.yaxis.get_label().get_position()[1]
            ax.yaxis.set_label_coords(ax_x, ax_y)
            ax.yaxis.get_label().set_ma("center")
            # probably some bug
            if matplotlib.__version__ < "1.2.1":
                ax.yaxis.get_label().set_va("center")
            else:
                ax.yaxis.get_label().set_va("bottom")

    def _axes_align(self):
        """Align all the ylabels which are on the same col"""
        ylabel_col = collections.defaultdict(list)
        for ax in self.get_new_axes():
            left = (True if
                    ax.yaxis.get_ticks_position() in ("left", "default") else
                    False)
            ylabel_col[(ax.min_col, left)].append(ax)

        for (_col, left), axes in ylabel_col.items():
            self.__axes_align_col(axes, left)

    def latex(self, text, kwargs):
        """Add some latex"""

        if isinstance(text, (tuple, list, set)):
            text = [self.latex(elem, dict(kwargs)) for elem in text]
            return [elem[0] for elem in text], text[0][1]

        if not isinstance(text, six.string_types):
            text = "{0}".format(text)

        if matplotlib.rcParams["text.usetex"]:
            text = text.replace("-", "--")

            text = text.replace("%", r"\%")
            values = text.split("__")
            if "style" in kwargs and kwargs["style"] == "italic":
                values = ["\\textit{{{0}}}".format(text)
                          for text in values]
                del kwargs["style"]
            if "weight" in kwargs and kwargs["weight"] == "bold":
                values = ["\\textbf{{{0}}}".format(text)
                          for text in values]
                del kwargs["weight"]

            text = "\n".join(values)

        text = text.replace(">=", r"$\geq$")
        text = text.replace("<=", r"$\leq$")
        text = text.replace("<", r"$<$")
        text = text.replace(">", r"$>$")
        text = text.replace("__", "\n")
        return text, kwargs

    def add_line(self, line, label, leg_place="fig"):
        """Add a label for the legend"""

        label = "{0}".format(label).strip()
        label = self.latex(label, {})[0]
        if (isinstance(leg_place, six.string_types) and
                leg_place.startswith("ax")):
            leg_ax = line.get_new_axes()
            leg_place = (leg_ax.parent if leg_ax.parent is not None else
                         leg_ax)
        if (label not in self.labels[leg_place] and
                label != "" and
                leg_place not in (None, "none", "None")):
            self.plotlines[leg_place].append(line)
            self.labels[leg_place].append(label)
