import os
from functools import partial

import numpy as np
import panel as pn
import xarray as xr
import holoviews as hv
import geoviews as gv
import cartopy.crs as ccrs

from geoviews import Polygons
from earthsim.annotators import PolyAnnotator, paths_to_polys
from earthsim.grabcut import GrabCutPanel, SelectRegionPanel
from bokeh.io import curdoc

gv.extension('bokeh')

bounds = (-77.5, 34.45, -77.3, 34.75)

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

# Current state
state = select_region

def set_grabcut(img):
    """
    Instantiate GrabCut panel and replace it in the layout
    """
    global state
    dashboard = GrabCutPanel(img, width=400)
    state = dashboard
    row[0] = pn.Row(dashboard.param, dashboard.view())
    
def load_image():
    """
    Loads the image updates the progress spinner and sets up a callback
    to show the GrabCut panel.
    """
    img = select_region.get_tiff()
    spinner_col[2] = '<center><b>Running GrabCut<b></center>'
    curdoc().add_next_tick_callback(partial(set_grabcut, img))

def next(event):
    """
    Switches from SelectRegionPanel to GrabCutPanel
    """
    global state
    if state is select_region:
        prev_button.disabled = False
        spinner_col[2] = '<center><b>Downloading tiff<b></center>'
        row[0] = spinner_layout
        curdoc().add_next_tick_callback(load_image)
    elif isinstance(state, GrabCutPanel):
        annotator = PolyAnnotator(polys=state.result)
        state = annotator
        row[0] = annotator.panel()
    elif isinstance(state, PolyAnnotator):
        next_button.disabled = True
        state = paths_to_polys(state.poly_stream.element)
        row[0] = state.options(width=500, height=500)
next_button.param.watch(next, 'clicks')

def previous(event):
    """
    Go back from the GrabCutPanel to the SelectRegionPanel
    """
    global state
    if isinstance(state, (PolyAnnotator, Polygons)):
        next_button.disabled = False
        spinner_col[2] = '<center><b>Downloading tiff<b></center>'
        row[0] = spinner_layout
        curdoc().add_next_tick_callback(load_image)
    elif isinstance(state, GrabCutPanel):
        prev_button.disabled = True
        row[0] = select_panel
        state = select_panel
prev_button.param.watch(previous, 'clicks')

row.servable()
