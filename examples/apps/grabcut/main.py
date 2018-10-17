import os
from functools import partial

import numpy as np
import panel as pn
import xarray as xr
import holoviews as hv
import geoviews as gv
import cartopy.crs as ccrs
from earthsim.annotators import PolyAndPointAnnotator
from earthsim.grabcut import GrabCutPanel, SelectRegionPanel
from bokeh.io import curdoc

gv.extension('bokeh')

bounds = (-77.5, 34.45, -77.3, 34.75)
background = np.array([
    [-77.3777271 , 34.66037492], [-77.35987035, 34.62251189], [-77.34130751, 34.64016586],
    [-77.35563287, 34.65360275], [-77.36083954, 34.66560481], [-77.3777271 , 34.66037492]
])
foreground = np.array([
    [-77.46585666, 34.66965009], [-77.46451121, 34.62795592], [-77.43105867, 34.64501054],
    [-77.41376085, 34.62573423], [-77.37886112,34.63780581], [-77.41283172, 34.6800562 ],
    [-77.46585666, 34.66965009]
])

# Declare SelectRegion panel
select_region = SelectRegionPanel(hv.Bounds(bounds), magnification=1)
select_panel = pn.Row(select_region.param, select_region.view())

# Declare Previous/Next buttons
prev_button = pn.widgets.Button(name='Previous', disabled=True)
next_button = pn.widgets.Button(name='Next')

# Declare spinner
spinner = pn.Pane(os.path.join(os.path.dirname(__file__), 'spinner.gif'))
spinner_col = pn.Column(pn.Spacer(height=200), spinner, '')
spinner_layout = pn.Row(pn.Spacer(width=500), spinner_col, pn.Spacer(width=500))

# Root panel
row = pn.Row(select_panel, pn.Column(prev_button, next_button))

def set_grabcut(img):
    """
    Instantiate GrabCut panel and replace it in the layout
    """
    dashboard = GrabCutPanel(img, fg_data=[foreground], bg_data=[background], width=400)
    row[0] = pn.Row(dashboard.param, dashboard.view())
    
def load_image():
    """
    Loads the image updates the progress spinner and sets up a callback
    to show the GrabCut panel
    """
    img = select_region.get_tiff()
    spinner_col[2] = '<center><b>Running GrabCut<b></center>'
    curdoc().add_next_tick_callback(partial(set_grabcut, img))
    
def next(event):
    """
    Switches from SelectRegionPanel to GrabCutPanel
    """
    prev_button.disabled = False
    next_button.disabled = True
    spinner_col[2] = '<center><b>Downloading tiff<b></center>'
    row[0] = spinner_layout
    curdoc().add_next_tick_callback(load_image)
next_button.param.watch(next, 'clicks')

def previous(event):
    """
    Go back from the GrabCutPanel to the SelectRegionPanel
    """
    prev_button.disabled = True
    next_button.disabled = False
    row[0] = select_panel
prev_button.param.watch(previous, 'clicks')

row.servable()
