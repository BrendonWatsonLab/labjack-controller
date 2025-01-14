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

import random

## Function definitions:
def backup(labjack: LabjackReader, filename: str, num_seconds: int) -> None:
    """
    Simple function to backup all data into a pickle.

    Parameters
    ----------
    labjack: LabjackReader
        A LabjackReader that is collecting data at the
        time of this function's call.
    filename: str
        The name of the file to write to.
        If it does not exist yet, it will be created.
    num_seconds: int
        The number of seconds to try live backup.
        After this time, write any remaining data in
        the labjack's buffer.

    Returns
    -------
    None

    """
    start_time = time.time()
    # Write data until time is up.
    while time.time() - start_time <= num_seconds:
        if not (time.time() - start_time) % 60:
            print("Backup at", time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
            labjack.to_dataframe().to_pickle(filename)

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





##
#################### END FUNCTION DEFININTIONS BLOCK



#
#### Set the desired Labjack Stream settings:
## Example 1:
# duration = 10  # seconds
# frequency = 100  # sampling frequency in Hz
# channels = ["AIN0", "AIN1", "DIO1"]  # read Analog INput 0, Digital INput 1.
# analog_voltages = [10.0]  # i.e. read input voltages from -10 to 10 volts

device_type = "T7"
connection_type = "USB"
duration = 15  # seconds
freq = 100  # sampling frequency in Hz
# channels = ["AIN0", "AIN1", "AIN2", "AIN3"]
channels = ["AIN0", "AIN1", "AIN2", "AIN3", "FIO0", "FIO1", "FIO2", "FIO3"] # Pho Home Testing Port Config
# channels = ["EIO0", "EIO1", "EIO2", "EIO3", "EIO4", "EIO5", "EIO6", "EIO7", "AIN0"] # BB-16 Port config
num_channels = len(channels)

analog_voltages = [10.0, 10.0, 10.0, 10.0]  # i.e. read input analog_voltages from -10 to 10 volts, only used for analog voltages
# analog_voltages = [10.0]  # i.e. read input analog_voltages from -10 to 10 volts, only used for analog voltages

# BaseManagers can be used to share complex objects, attributes and all, across multiple processes.
BaseManager.register('LabjackReader', LabjackReader)

if __name__ == '__main__':
    manager = BaseManager()
    manager.start()

    # Instantiate a shared LabjackReader
    my_lj = manager.LabjackReader(device_type, connection_type=connection_type)

    ## declare the functions we want to run in parallel:
    #    Declare a data-gathering process
    data_proc = Process(target=my_lj.collect_data,
                        args=(channels, analog_voltages, duration, freq),
                        kwargs={'resolution': 1, 'scans_per_read': 1})

    #    Declare a data backup process
    backup_proc = Process(target=backup, args=(my_lj, "backup.pkl",
                                            duration))


    ## BEGIN MAIN RUN:
    # Start all threads, and join when finished.
    data_proc.start()
    backup_proc.start()

    p = figure(plot_width=400, plot_height=400)
    r1 = p.line([], [], color="firebrick", line_width=2)
    r2 = p.line([], [], color="navy", line_width=2)

    ds1 = r1.data_source
    ds2 = r2.data_source

    @linear()
    def update_live_plot(step):
        ds1.data['x'].append(step)
        ds1.data['y'].append(random.randint(0,100))
        ds2.data['x'].append(step)
        ds2.data['y'].append(random.randint(0,100))  
        ds1.trigger('data', ds1.data, ds1.data)
        ds2.trigger('data', ds2.data, ds2.data)

    ## Build Live Plot:
    curdoc().add_root(p)

    # Add a periodic callback to be run every 500 milliseconds
    curdoc().add_periodic_callback(update_live_plot, 500)





    ## .join() waits for both processes to be complete before moving on with the code's execution
    data_proc.join()
    backup_proc.join()

    datarun = my_lj.to_dataframe()
    # Get all data recorded as a 2D Numpy array
    my_data = my_lj.to_array()

    # Explicitly close the connection?
    # We do need to explicitly close the connection when we don't want it anymore.
    my_lj.close()


    # advancedPlotResultFrame(datarun, channels)



    # # Instantiate a LabjackReader
    # start = time.time_ns()

    # with LabjackReader("T7") as my_lj:
    #     my_lj.collect_data(channels, analog_voltages, duration, frequency)

    #     # my_lj.collect_data(channels, analog_voltages, duration, frequency, 
    #     #                     callback_function=print_row, num_threads=16)

    #     datarun_source = my_lj.to_dataframe()
    #     print("Actual time took: %f seconds" % ((time.time_ns() - start) / 1e9))

    #  # Get the data we collected.
    # print(datarun_source)

    # plotResultFrame(datarun_source)
