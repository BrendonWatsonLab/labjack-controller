# phoWebCSVDataViewer.py
# Pho Hale, 05-27-2021 @ 4:04pm
# This file opens a stream to a Labjack T7 connected over USB, reading its specified pins at a high frequency for the specified duration.
# It makes use of the labjack-controller 3rd party python library: https://labjack-controller.readthedocs.io/en/latest/


# Potential next steps:
# Integrate LabStreamingReciever to enable asynchronous writes out to .csv and updating of a plot:  https://github.com/CommanderPho/PhoLabStreamingReceiver/blob/master/PhoLabStreamingReceiver.py

## TODO:
# Implement hover crosshairs: https://discourse.bokeh.org/t/mouse-vertical-line-on-linked-plots/2449/7


import pandas as pd
import matplotlib.pyplot as plt
from labjackcontroller.labtools import LabjackReader

from multiprocessing.managers import BaseManager
from multiprocessing import Process

import time

from bokeh.models.widgets import DataTable, TableColumn
from bokeh.models import ColumnDataSource
from bokeh.models import CustomJS, Span, CrosshairTool, HoverTool, ResetTool, PanTool, WheelZoomTool # For live crosshairs

# from bokeh.palettes import SpectralColorScheme, Spectral9
from bokeh.palettes import Spectral11 as SpectralColorScheme
from bokeh.plotting import figure, show, gridplot, curdoc
from bokeh.driving import linear
from bokeh.layouts import column

# from random import random
from random import random, randint

# csv_watch_path = "C:/Users/Pho/repos/labjack-controller/backup.csv"
csv_watch_path = "STREAMING_CSV.csv"

## Function definitions:

## Live Plotting Functions:

def addLinkedCrosshairs(plots):
    js_move = '''   start = fig.x_range.start, end = fig.x_range.end
                    if(cb_obj.x>=start && cb_obj.x<=end && cb_obj.y>=start && cb_obj.y<=end)
                        { cross.spans.height.computed_location=cb_obj.sx }
                    else { cross.spans.height.computed_location = null }
                    if(cb_obj.y>=start && cb_obj.y<=end && cb_obj.x>=start && cb_obj.x<=end)
                        { cross.spans.width.computed_location=cb_obj.sy  }
                    else { cross.spans.width.computed_location=null }'''
    js_leave = '''cross.spans.height.computed_location=null; cross.spans.width.computed_location=null'''

    figures = plots[:]
    for plot in plots:
        crosshair = CrosshairTool(dimensions = 'both')
        plot.add_tools(crosshair)
        for figure in figures:
            if figure != plot:
                args = {'cross': crosshair, 'fig': figure}
                figure.js_on_event('mousemove', CustomJS(args = args, code = js_move))
                figure.js_on_event('mouseleave', CustomJS(args = args, code = js_leave))


def add_vlinked_crosshairs(figs):
    js_leave = ''
    js_move = 'if(cb_obj.x >= fig.x_range.start && cb_obj.x <= fig.x_range.end &&\n'
    js_move += 'cb_obj.y >= fig.y_range.start && cb_obj.y <= fig.y_range.end){\n'
    for i in range(len(figs)-1):
        js_move += '\t\t\tother%d.spans.height.computed_location = cb_obj.sx\n' % i
    js_move += '}else{\n'
    for i in range(len(figs)-1):
        js_move += '\t\t\tother%d.spans.height.computed_location = null\n' % i
        js_leave += '\t\t\tother%d.spans.height.computed_location = null\n' % i
    js_move += '}'
    crosses = [CrosshairTool() for fig in figs]
    for i, fig in enumerate(figs):
        fig.add_tools(crosses[i])
        args = {'fig': fig}
        k = 0
        for j in range(len(figs)):
            if i != j:
                args['other%d'%k] = crosses[j]
                k += 1
        fig.js_on_event('mousemove', CustomJS(args=args, code=js_move))
        fig.js_on_event('mouseleave', CustomJS(args=args, code=js_leave))


##
#################### END FUNCTION DEFININTIONS BLOCK

# if __name__ == '__main__':

# p = figure(plot_width=1024, plot_height=400)

# Read CSV to start to get the names
read_df = pd.read_csv(csv_watch_path)
data_columns = read_df.columns[:-2].values # Get all but the last two elements, which are the times
num_columns = len(data_columns)
# print(data_columns)

figure_list = list()
datasource_list = list()

# Multi figure version:
# for column_name in data_columns:
for i, column_name in enumerate(data_columns):
	curr_is_first_fig = (i == 0)
	curr_is_last_fig = (i == (num_columns - 1))

	# TOOLS = [CrosshairTool(dimensions = 'height'), PanTool(dimensions = 'width'), HoverTool(tooltips = [("Date", "@t")]), WheelZoomTool(dimensions = 'width'), ResetTool()]
	TOOLS = [PanTool(dimensions = 'width'), HoverTool(tooltips = [("Date", "@x")]), WheelZoomTool(dimensions = 'width'), ResetTool()]


	curr_fig = figure(plot_width=1024, plot_height=100, title=None, tools=TOOLS)
	curr_line = curr_fig.line([], [], color="firebrick", line_width=2)
	curr_ds = curr_line.data_source

	curr_fig.yaxis.axis_label = column_name

	curr_fig.axis.visible = False
	curr_fig.ygrid.visible = False

	curr_fig.yaxis.major_label_text_font_size = '0pt'  # turn off y-axis tick labels

	# change just some things about the y-grid
	curr_fig.ygrid.band_fill_alpha = 0.1
	curr_fig.ygrid.band_fill_color = "navy"

	curr_fig.x_range.follow = "end"

	if not curr_is_first_fig:
		# Set the x_range for this figure to that of the first figure:
		curr_fig.x_range = figure_list[0].x_range
		curr_fig.js_link('x_range', figure_list[0], 'x_range')



	figure_list.append(curr_fig)
	datasource_list.append(curr_ds)


# Add the crosshairs to the plots:
# addLinkedCrosshairs(figure_list)
add_vlinked_crosshairs(figure_list)

# @linear()
# def update_live_plot(step):
# 	ds1.data['x'].append(step)
# 	ds1.data['y'].append(randint(0,100))
# 	ds2.data['x'].append(step)
# 	ds2.data['y'].append(randint(0,100))  
# 	ds1.trigger('data', ds1.data, ds1.data)
# 	ds2.trigger('data', ds2.data, ds2.data)


@linear()
def update_live_plot(step):
	read_df = pd.read_csv(csv_watch_path)

	# print(read_df.columns)
	data_columns = read_df.columns[:-2].values # Get all but the last two elements, which are the times
	num_columns = len(data_columns)

	# print(data_columns)
	# print(data_columns)
	# Get python dictionary from dataframe:
	# new_data = dict()
	# new_data['x'] = read_df['System Time']
	# new_data['y'] = read_df['AIN0']
	# # new_data['y'] = read_df[['AIN0','AIN1']]
	# ds1.data = new_data

	# new_data = dict()
	# new_data['x'] = read_df['System Time']
	# # new_data['y'] = read_df['AIN0']
	# new_data['y'] = read_df['AIN1']
	# ds1.data = new_data

	# # ds1.data['x'].append(step)
	# # ds1.data['y'].append(randint(0,100))
	# # ds2.data['x'].append(step)
	# # ds2.data['y'].append(randint(0,100))  
	# ds1.trigger('data', ds1.data, ds1.data)
	# ds2.trigger('data', ds2.data, ds2.data)


	# for column_name in data_columns:
	# for i in range(num_columns):
	for i, curr_col_name in enumerate(data_columns):
		# curr_col_name = data_columns[i]
		curr_new_data = dict()
		curr_new_data['x'] = read_df['System Time']
		curr_new_data['y'] = read_df[curr_col_name]
		datasource_list[i].data = curr_new_data
		datasource_list[i].trigger('data', datasource_list[i].data, datasource_list[i].data)


## Build Live Plot:
# curdoc().add_root(p)

curdoc().add_root(column(figure_list, merge_tools=True))


# Add a periodic callback to be run every 2000 milliseconds
curdoc().add_periodic_callback(update_live_plot, 2000)



