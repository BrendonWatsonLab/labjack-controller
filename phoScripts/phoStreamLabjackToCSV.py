# phoStreamLabjackToCSV.py
# Pho Hale, 05-26-2021 @ 10:12pm
# This file opens a stream to a Labjack T7 connected over USB, reading its specified pins at a high frequency for the specified duration.
# It makes use of the labjack-controller 3rd party python library: https://labjack-controller.readthedocs.io/en/latest/

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
from bokeh.plotting import figure, show, gridplot

## Function definitions:
def backup(labjack: LabjackReader, basename: str, num_seconds: int) -> None:
	"""
	Simple function to backup all data into a pickle.

	Parameters
	----------
	labjack: LabjackReader
		A LabjackReader that is collecting data at the
		time of this function's call.
	basename: str
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
		time.sleep(0.25) # Waste a second before updating the .csv again
		curr_time = time.time()
		curr_rel_time = curr_time - start_time
		# if not (curr_rel_time) % 60:
		# if (curr_rel_time) % 60:
		
		curr_df = labjack.to_dataframe()
		if (len(curr_df.columns) > 2):
			# Convert the analog columns into digital
			# print("test channels access: {}\n should_discretize: {}".format(channels, should_discretize_analog_channel))
			if is_pho_home_config:
				## TODO: See https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy to fix annoying error
				sub_df = curr_df.iloc[:, 0:4] # TODO: hardcoded the analog channels 0:4
				# print("test: {}".format(sub_df))
				found_idx = sub_df.gt(2.5).copy()
				# This should update curr_df too, since sub_df is not a copy
				sub_df.iloc[found_idx] = 1
				sub_df.iloc[~found_idx] = 0
			
			# curr_df.to_pickle(basename + '.pkl')
			csv_output_final_filename = basename + '.csv'

			print("Backup at", time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
			curr_df.to_csv(csv_output_final_filename, encoding='utf-8', index=False)
			print('\t updated {}'.format(csv_output_final_filename))
		else:
			print('\t Input not set up yet at', time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))


##
#################### END FUNCTION DEFININTIONS BLOCK



#
#### Set the desired Labjack Stream settings:
## Example 1:
# duration = 10  # seconds
# frequency = 100  # sampling frequency in Hz
# channels = ["AIN0", "AIN1", "DIO1"]  # read Analog INput 0, Digital INput 1.
# analog_voltages = [10.0]  # i.e. read input voltages from -10 to 10 volts

streaming_csv_output_basename = "STREAMING_CSV"
device_type = "T7"
connection_type = "USB"
duration = 90  # seconds
freq = 100  # sampling frequency in Hz



## BB-16 config:
is_pho_home_config = False
channels = ["EIO0", "EIO1", "EIO2", "EIO3", "EIO4", "EIO5", "EIO6", "EIO7", "AIN0"] # BB-16 Port config
analog_voltages = [10.0]  # i.e. read input analog_voltages from -10 to 10 volts, only used for analog voltages

## Pho Home Testing Config:
# is_pho_home_config = True
# channels = ["AIN0", "AIN1", "AIN2", "AIN3", "FIO0", "FIO1", "FIO2", "FIO3"] # Pho Home Testing Port Config
# analog_voltages = [10.0, 10.0, 10.0, 10.0]  # i.e. read input analog_voltages from -10 to 10 volts, only used for analog voltages

num_channels = len(channels)

# BaseManagers can be used to share complex objects, attributes and all, across multiple processes.
BaseManager.register('LabjackReader', LabjackReader)

def labjackAcqMain():
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
	backup_proc = Process(target=backup, args=(my_lj, streaming_csv_output_basename, duration))


	## BEGIN MAIN RUN:
	# Start all threads, and join when finished.
	data_proc.start()
	backup_proc.start()

	## .join() waits for both processes to be complete before moving on with the code's execution
	data_proc.join()
	backup_proc.join()

	# datarun = my_lj.to_dataframe()
	# # Get all data recorded as a 2D Numpy array
	# my_data = my_lj.to_array()

	# Explicitly close the connection?
	# We do need to explicitly close the connection when we don't want it anymore.
	my_lj.close()


if __name__ == '__main__':
	labjackAcqMain()
