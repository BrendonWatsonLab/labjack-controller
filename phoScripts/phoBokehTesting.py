# Pho Hale, 05-27-2021 @ 4:04pm
# This file opens a stream to a Labjack T7 connected over USB, reading its specified pins at a high frequency for the specified duration.
# It makes use of the labjack-controller 3rd party python library: https://labjack-controller.readthedocs.io/en/latest/


# Potential next steps:
# Integrate LabStreamingReciever to enable asynchronous writes out to .csv and updating of a plot:  https://github.com/CommanderPho/PhoLabStreamingReceiver/blob/master/PhoLabStreamingReceiver.py


import pandas as pd
import matplotlib.pyplot as plt
from labjackcontroller.labtools import LabjackReader

from multiprocessing.managers import BaseManager
from multiprocessing import Process

import time

from bokeh.models.widgets import DataTable, TableColumn
from bokeh.models import ColumnDataSource
# from bokeh.palettes import SpectralColorScheme, Spectral9
from bokeh.palettes import Spectral11 as SpectralColorScheme
from bokeh.plotting import figure, show, gridplot, curdoc
from bokeh.driving import linear

# from random import random
from random import random, randint

csv_watch_path = "C:/Users/Pho/repos/labjack-controller/backup.csv"

## Function definitions:

def print_row(row):
    print(row)

def plotResultFrame(df):
    fig_width = 800
    tools = ["box_select", "box_zoom", "hover", "reset"]
    datarun_source = ColumnDataSource(my_lj.to_dataframe()[4:])
    time_fig = figure(plot_width=fig_width, title="Time vs. System Time",
                    x_axis_label="Device Time (sec)", y_axis_label="System Time (Sec)", tools=tools)
    time_fig.line(source=datarun_source, x="Time", y="System Time")

    show(time_fig)
    return time_fig


def advancedPlotResultFrame(df, ports):
    # Creates an advanced plot that shows the state of signals logged during the run
    fig_width = 800
    tools = ["box_select", "box_zoom", "hover", "reset"]

    # ports = ["AIN0", "AIN1", "AIN2", "AIN3"]
    num_ports = len(ports)
    subplot_height = num_ports * 100


    datarun_source = ColumnDataSource(datarun[num_ports:])
    # Table plot
    Columns = [TableColumn(field=Ci, title=Ci) for Ci in datarun.columns]  # bokeh columns
    data_table = DataTable(columns=Columns, source=datarun_source, width=fig_width)  # bokeh table

    # Time graph
    time_fig = figure(plot_width=fig_width, title="Time vs. System Time",
                    x_axis_label="Device Time (sec)", y_axis_label="System Time (Sec)", tools=tools)
    time_fig.line(source=datarun_source, x="Time", y="System Time")

    # AIN0..N vs device time graph
    data_time_fig = figure(plot_width=fig_width, plot_height=subplot_height, title="AIN0-N vs Device Time",
                        x_axis_label="Device Time (sec)", y_axis_label="Voltage (V)", tools=tools)
    for i, column in enumerate(ports):
        data_time_fig.line(source=datarun_source, x="Time", y=column, line_width=1, color=SpectralColorScheme[i + 2],
                        alpha=0.8, muted_color=SpectralColorScheme[i + 2], muted_alpha=0.075,
                        legend=column + " Column")
        data_time_fig.circle(source=datarun_source, x="Time", y=column, line_width=1, color=SpectralColorScheme[i + 2],
                            alpha=0.8, muted_color=SpectralColorScheme[i + 2], muted_alpha=0.075,
                            legend=column + " Column", size=1)


    # data_time_fig.x_range.start = x
    data_time_fig.legend.location = "top_left"
    data_time_fig.legend.click_policy="mute"

    # AIN0..N vs system time graph
    data_sys_time_fig = figure(plot_width=fig_width, plot_height=subplot_height, title="AIN0-N vs System Time",
                            x_axis_label="System Time (sec)", y_axis_label="Voltage (V)", tools=tools)
    for i, column in enumerate(ports):
        data_sys_time_fig.line(source=datarun_source, x="System Time", y=column, line_width=1, color=SpectralColorScheme[i + 2],
                            alpha=0.8, muted_color=SpectralColorScheme[i + 2], muted_alpha=0.075,
                            legend=column + " Column")
        data_sys_time_fig.circle(source=datarun_source, x="System Time", y=column, line_width=1, color=SpectralColorScheme[i + 2],
                                alpha=0.8, muted_color=SpectralColorScheme[i + 2], muted_alpha=0.075,
                                legend=column + " Column", size=1)

    data_sys_time_fig.legend.location = "top_left"
    data_sys_time_fig.legend.click_policy="mute"

    # Organize and show all plots.
    p = gridplot([[data_sys_time_fig], [data_time_fig], [data_table], [time_fig]])

    show(p)

## Live Plotting Functions:

# aapl = pd.read_csv(data_paths[0])



##
#################### END FUNCTION DEFININTIONS BLOCK

# if __name__ == '__main__':

p = figure(plot_width=400, plot_height=400)
r1 = p.line([], [], color="firebrick", line_width=2)
r2 = p.line([], [], color="navy", line_width=2)

ds1 = r1.data_source
ds2 = r2.data_source

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

	print(read_df.columns)
	# Get python dictionary from dataframe:
	new_data = dict()
	new_data['x'] = read_df['System Time']
	new_data['y'] = read_df['AIN0']

	ds1.data = new_data

	# ds1.data['x'].append(step)
	# ds1.data['y'].append(randint(0,100))
	# ds2.data['x'].append(step)
	# ds2.data['y'].append(randint(0,100))  
	ds1.trigger('data', ds1.data, ds1.data)
	ds2.trigger('data', ds2.data, ds2.data)


## Build Live Plot:
curdoc().add_root(p)

# Add a periodic callback to be run every 2000 milliseconds
curdoc().add_periodic_callback(update_live_plot, 2000)



