## Installing:



### Open two Anaconda Consoles and change the environment to labjack-controller
`conda activate labjack-controller`

### Change Directory to the "phoScripts" subdirectory in repo you checked out in both Consoles:
`cd phoScripts`

### In console 1: execute
`python phoStreamLabjackToCSV.py`

### In console 2: execute
`bokeh serve --show phoWebCSVDataViewer.py`
This will load the csv output from the console 1 process and refresh it every so often to update the plot.


## Data Streamer Component:
python phoStreamLabjackToCSV.py
Outputs the csv file in the directory the script is executed in

## Data Viewer Component:
Make sure to change the csv_watch_path to the location of the .csv file produced by the data streamer component
bokeh serve --show phoBokehTesting.py