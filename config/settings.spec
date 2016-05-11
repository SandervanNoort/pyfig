# title of the figure
title = string(default="")

# location of the title
title_loc = option("left", "center", default="center")

# location of the legend
legend_loc = option("left", "right", "top", "bottom", "outer right", "outer left", "outer top", "outer bottom", "upper right", "upper left", "outer rowcol", "", default="outer right")

# row,col location of the legend
legend_rowcol = int_list(default=list())

# number of columns in the figure (0: automatically resize to fit)
ncol = integer(default=1)

# language (controls the name of months in date-axes
lang = option("en", "nl", "pt", default="en")

# name of the figure
figname = string(default="default")

# the size in 100-pixels: 6,4 => width=600px x height=400px
figsize = float_list(min=2, max=2, default=list(6,3.5))

# dots per inch
dpi = integer(default=100)

# background color of the figure
facecolor = string(default="white")

# bottomleft text
url = string(default="")

# bottom right text
date = string(default="")

# have open axes
ax_open = boolean(default=false)

# image printed in bottom left, before the url
logo = string(default="")

# update the plot commands which have color/linestyle/marker=mix, linewidth=1
colors = string_list(default=list("blue", "green", "red", "cyan", "magenta", "yellow", "brown", "orange", "pink", "purple", "lightblue", "lightgreen", "0.5", "black"))
# markers = string_list(default=list("+", "x", "1", "s", "o", "^", "D"))

# the floats with the row division
rows = float_list(default=list(1))
# the floats with the col division
cols = float_list(default=list(1))

# size and style of the ax label
ax_label_style = string(default="italic")

# only have an x-label from the bottom-most axes
bottom_labels = boolean(default=False)

# only have xticks on the bottom-most axes
bottom_xticks = boolean(default=True)

# only have an y-label for the left-most axes
left_labels = boolean(default=False)

# Use different ticks and ticklabels for each ax (even if only one ylabel)
left_yticks = boolean(default=True)

# Use different ticks and ticklabels for each ax (even if only one ylabel)
right_yticks = boolean(default=True)

# use only a single ylabel
single_ylabel = boolean(default=False)

# use only a single ylabel
single_xlabel = boolean(default=False)

# only have an y-label for the right-most axes
right_labels = boolean(default=False)

# only have a single y-label for multiple stacked axes on top of each other
single_left_label = boolean(default=False)

# a label for the ax (written inside the frame)
ax_labels = boolean(default=True)

# all axes are numbered a,b,c etc.
abc_labels = boolean(default=False)

# the alignment of the abc label compared to the left-top of ax-frame
abc_align = option("center", "top", "bottom", default="center")

# if reversed, first number down along the column
abc_reverse = boolean(default=False)

# remove the top tick from all the axes (mostly together with abc_labels)
remove_toptick = boolean(default=False)

# align the y-labels
axes_align = boolean(default=True)

# enlarge the whole figure to include legends
resize = boolean(default=False)

[rc]
#     font.family = string(default="Palatino")
    font.family = string(default="Ubuntu")
#     font.serif = string(default="Palatino")
#     font.family = string(default="Arial")
#    font.family = string(default="Helvetica")
    xtick.labelsize = integer(default=9)
    ytick.labelsize = integer(default=8)
    ytick.minor.pad = integer(default=2)
    ytick.major.pad = integer(default=3)

    axes.labelsize = integer(default=11)
    axes.titlesize = integer(default=14)

    lines.linewidth = float(default=1.5)
    lines.markersize = float(default=4)

    legend.fontsize = integer(default=11)
    legend.shadow = boolean(default=False)
    legend.numpoints = integer(default=3)
    legend.handlelength = float(default=2.5)
    legend.markerscale = integer(default=1)

    legend.handletextpad = float(default=0.1)
    legend.columnspacing = float(default=0.8)
[margins]
    figure = int_list(default=list(5, 5, 5, 5))
    title = integer(default=0)
    title_row = integer(default=3)
    xticks = integer(default=20)
    xlabel = integer(default=20)
    yticks = integer(default=20)
    ylabel = integer(default=20)
    ax = integer(default=5)
    ax_col = integer(default=10)
    ax_row = integer(default=5)
    legend_row = integer(default=5)
    legend_col = integer(default=5)
    abc = integer(default=4)
    ax_label_size = integer(default=10)
