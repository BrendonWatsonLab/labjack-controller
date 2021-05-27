from functools import partial
from random import random
# from threading import Thread
import time

from bokeh.models import ColumnDataSource
from bokeh.plotting import curdoc, figure

from tornado import gen


## Labjack Inputs:
import pandas as pd
import matplotlib.pyplot as plt
from labjackcontroller.labtools import LabjackReader

from multiprocessing.managers import BaseManager
from multiprocessing import Process

from table_logger import TableLogger
# tbl = TableLogger(columns='a,b,c,d')
# tbl = TableLogger(columns=["AIN0", "AIN1", "AIN2", "AIN3", "FIO0", "FIO1", "FIO2", "FIO3","TIME","SYSTEM_TIME"].join(','))


## BOKEH SETUP:

# only modify from a Bokeh session callback
source = ColumnDataSource(data=dict(x=[0], y=[0]))

# This is important! Save curdoc() to make sure all threads
# see the same document.
doc = curdoc()

@gen.coroutine
def update(x, y):
    source.stream(dict(x=[x], y=[y]), 4096)

# def blocking_task():
#     while True:
#         # do some blocking computation
#         time.sleep(0.1)
#         x, y = random(), random()

#         # but update the document from a callback
#         doc.add_next_tick_callback(partial(update, x=x, y=y))



## Function definitions:

def on_labjack_data_row_received(row):
    # print(row)
    # Output to CSV:
    tbl(row)

    t = row[-1] # The timestamp is the last element of the row
    data_values = row[:-2] # The data values are all but the last two elements of the row
    x, y = t, data_values[0] # Get the first item only currently

    # print('trying to add (@, @)', x, y)
    print('trying to add ({}, {})'.format(x, y))

    # but update the document from a callback
    doc.add_next_tick_callback(partial(update, x=x, y=y))


# p = figure(x_range=[0, 1], y_range=[0,1])
# l = p.circle(x='x', y='y', source=source)

# doc.add_root(p)

# thread = Thread(target=blocking_task)
# thread.start()



##
#################### LABJACK FUNCTIONALITY:

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
            # labjack.to_dataframe().to_pickle(filename)
            labjack.to_dataframe().to_csv(filename)




def startWebServerCallback() -> None:
    print('Adding document root...')
    p = figure(x_range=[0, 1], y_range=[0, 1])
    # p.x_range.follow = "end"
    # p.x_range.follow_interval = 20
    # p.x_range.range_padding = 0
    l = p.circle(x='x', y='y', source=source)
    doc.add_root(p)


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
# channels = ["AIN0", "AIN1", "AIN2", "AIN3", "FIO0", "FIO1", "FIO2", "FIO3"] # Pho Home Testing Port Config
channels = ["EIO0", "EIO1", "EIO2", "EIO3", "EIO4", "EIO5", "EIO6", "EIO7", "AIN0"] # BB-16 Port config
num_channels = len(channels)

# tbl = TableLogger(columns=["AIN0", "AIN1", "AIN2", "AIN3", "FIO0", "FIO1", "FIO2", "FIO3","TIME","SYSTEM_TIME"].join(','))
columns_string = "{},TIME,SYSTEM_TIME".format(','.join(channels))

print('columns_string: {}'.format(columns_string))

active_csv_file = open("liveData.csv", "wb")
tbl = TableLogger(file=active_csv_file, csv=True, columns=columns_string)



# analog_voltages = [10.0, 10.0, 10.0, 10.0]  # i.e. read input analog_voltages from -10 to 10 volts, only used for analog voltages
analog_voltages = [10.0]  # i.e. read input analog_voltages from -10 to 10 volts, only used for analog voltages

# BaseManagers can be used to share complex objects, attributes and all, across multiple processes.
BaseManager.register('LabjackReader', LabjackReader)



def mainRun():
    manager = BaseManager()
    # print('Starting up labjack with ...')
    print('Starting up labjack with {} ports...'.format(num_channels))
    manager.start()

    # Instantiate a shared LabjackReader
    my_lj = manager.LabjackReader(device_type, connection_type=connection_type)

    ## declare the functions we want to run in parallel:
    #    Declare a data-gathering process
    data_proc = Process(target=my_lj.collect_data,
                        args=(channels, analog_voltages, duration, freq),
                        kwargs={'resolution': 1, 'scans_per_read': 1, 'callback_function': on_labjack_data_row_received})

    #    Declare a data backup process
    backup_proc = Process(target=backup, args=(my_lj, "backup.csv",
                                            duration))

    #    Declare a bokeh webserver process
    # bokeh_proc = Process(target=startWebServerCallback, args=())

    startWebServerCallback()

    ## BEGIN MAIN RUN:
    # Start all threads, and join when finished.

    print('Starting up data collection process...')
    data_proc.start()
    # bokeh_proc.start()
    backup_proc.start()

    ## .join() waits for both processes to be complete before moving on with the code's execution
    data_proc.join()
    # bokeh_proc.join()
    backup_proc.join()

    # datarun = my_lj.to_dataframe()
    # # Get all data recorded as a 2D Numpy array
    # my_data = my_lj.to_array()

    # Explicitly close the connection?
    # We do need to explicitly close the connection when we don't want it anymore.
    my_lj.close()

    active_csv_file.close()


# mainRun()

if __name__ == '__main__':
    mainRun()



