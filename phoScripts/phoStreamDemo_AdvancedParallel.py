# Pho Hale, 05-26-2021 @ 10:12pm
# This file opens a stream to a Labjack T7 connected over USB, reading its specified pins at a high frequency for the specified duration.
# It makes use of the labjack-controller 3rd party python library: https://labjack-controller.readthedocs.io/en/latest/


# Potential next steps:
# Integrate LabStreamingReciever to enable asynchronous writes out to .csv and updating of a plot:  https://github.com/CommanderPho/PhoLabStreamingReceiver/blob/master/PhoLabStreamingReceiver.py


import pandas as pd
import matplotlib.pyplot as plt
from labjackcontroller.labtools import LabjackReader

from multiprocessing.managers import BaseManager
from multiprocessing import Process, Queue

import time

from bokeh.models.widgets import DataTable, TableColumn
from bokeh.models import ColumnDataSource
# from bokeh.palettes import SpectralColorScheme, Spectral9
from bokeh.palettes import Spectral11 as SpectralColorScheme
from bokeh.plotting import figure, show, gridplot

# CSV Output
# from table_logger import TableLogger

# to_write_queue = Queue(128)

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

# Setup CSV Outputs:
csv_header_columns = channels.copy()
csv_header_columns.extend(["TIME","SYSTEM_TIME"])
# csv_header_columns = ["AIN0", "AIN1", "AIN2", "AIN3", "FIO0", "FIO1", "FIO2", "FIO3", "TIME","SYSTEM_TIME"]

# columns_string = ','.join(csv_header_columns)
# columns_string = "{},TIME,SYSTEM_TIME".format(','.join(channels))

# BaseManagers can be used to share complex objects, attributes and all, across multiple processes.
BaseManager.register('LabjackReader', LabjackReader)





## Function definitions:

def writer():
    # global to_write_queue
    print('writer hit')
    # Call to_write.get() until it returns None
    for df in iter(to_write_queue.get, None):
        print('writer iterator...')
        with open('writer_result.csv', 'w+') as f:
            df.to_csv(f, header=False, index=False)



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
            # labjack.to_dataframe().to_csv(filename, encoding='utf-8', index=False)




def on_labjack_data_row_received(row):
    # global to_write_queue
    print(row)
    # Output to CSV:
    # tbl(row[:])
    
    # Build a dataframe out of the row:
    # row_df = pd.DataFrame(row, columns=csv_header_columns)
    # print(row_df)
    # to_write_queue.put(row_df) # Add the row to the write queue
    # writer()
    


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




##
#################### END FUNCTION DEFININTIONS BLOCK





if __name__ == '__main__':

    print(csv_header_columns)
    # print('columns_string: {}'.format(columns_string))
    # active_csv_file = open("liveData.csv", "w+")
    # tbl = TableLogger(file=active_csv_file, csv=True, columns=columns_string)

    manager = BaseManager()
    manager.start()

    # Instantiate a shared LabjackReader
    my_lj = manager.LabjackReader(device_type, connection_type=connection_type)

    ## declare the functions we want to run in parallel:
    #    Declare a data-gathering process
    data_proc = Process(target=my_lj.collect_data,
                        args=(channels, analog_voltages, duration, freq),
                        kwargs={'resolution': 1, 'scans_per_read': 1, 'callback_function': on_labjack_data_row_received})




    #    Declare a data backup process
    # backup_proc = Process(target=backup, args=(my_lj, "backup.csv", duration))

    # csv_logging_proc = Process(target=writer)
    # csv_logging_proc = Process(target=writer, args=(to_write))


    ## BEGIN MAIN RUN:
    # Start all threads, and join when finished.
    # Put the header on the file
    # to_write_queue.put(csv_header_columns)

    # csv_logging_proc.start()

    # # Put the header on the file
    # to_write.put(columns_string)

    print('Starting data_proc:')
    data_proc.start()
    # backup_proc.start()

    ## .join() waits for both processes to be complete before moving on with the code's execution
    data_proc.join()
    print('data_proc finished.')

    # # enqueue None to instruct the writer thread to exit
    # to_write_queue.put(None)
    # print('enqueued none so writer thread exits')

    # Wait for writer to exit
    # csv_logging_proc.join()
    # print('writer exited.')

    # backup_proc.join()

    # datarun = my_lj.to_dataframe()
    # # Get all data recorded as a 2D Numpy array
    # my_data = my_lj.to_array()

    print('writing out final csv to {}...'.format('final_backup.csv'))
    my_lj.to_dataframe().to_csv('final_backup.csv', encoding='utf-8', index=False)
    print('done.')

    # Explicitly close the connection?
    # We do need to explicitly close the connection when we don't want it anymore.
    my_lj.close()

    # tbl.close()
    # active_csv_file.close()

    # advancedPlotResultFrame(datarun, channels)
    print('all done!')


