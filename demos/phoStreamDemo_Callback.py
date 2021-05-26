import time
import pandas as pd
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure, show
from labjackcontroller.labtools import LabjackReader

duration = 10  # seconds
frequency = 100  # sampling frequency in Hz
channels = ["AIN0", "AIN1", "DIO1"]  # read Analog INput 0, Digital INput 1.

analog_voltages = [10.0]  # i.e. read input voltages from -10 to 10 volts

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



# Instantiate a LabjackReader
start = time.time_ns()

with LabjackReader("T7") as my_lj:
    my_lj.collect_data(channels, analog_voltages, duration, frequency)

    # my_lj.collect_data(channels, analog_voltages, duration, frequency, 
    #                     callback_function=print_row, num_threads=16)

    datarun_source = my_lj.to_dataframe()
    print("Actual time took: %f seconds" % ((time.time_ns() - start) / 1e9))



 # Get the data we collected.
print(datarun_source)

plotResultFrame(datarun_source)
