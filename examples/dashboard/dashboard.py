from pathlib import Path
from collections import OrderedDict

import math
import os
import param
import parambokeh

from app import App, DashboardLayout, ComposeLayouts, ColumnLayouts, DivLayout, shared_state


import numpy as np
import cartopy.crs as ccrs
import geoviews as gv
import xarray as xr
import holoviews as hv

import quest
from earthsim.grabcut import GrabCutDashboard, SelectRegionPlot


class SelectRegionWidgets(DashboardLayout):
    """
    Provides the Bokeh widgets for the region selection dashboard
    """

    def __init__(self, layout):
        self.layout = layout
        shared_state.set_state(tile_server=self.layout.plot.tile_server)

    def callback(self, obj, **kwargs):
        self.layout.plot.set_tile_server(obj.tile_server)
        shared_state.set_state(tile_server=obj.tile_server)


    def __call__(self, shared_state, doc):
        self.layout.plot.name = 'Settings'
        return parambokeh.Widgets(self.layout.plot, mode='raw',
                                  doc=doc, callback=self.callback)



class LaunchGrabCut(DashboardLayout):
    """
    The button to launch the grab cut dashboard, opening a new browser tab.
    """

    def __init__(self, select_region):
        self.button = GrabCutButton(select_region, name='Extract Coastline')

    def __call__(self, shared_state, doc):
        from bokeh.models.widgets import Button
        from bokeh.models.callbacks import CustomJS

        widgets = parambokeh.Widgets(self.button, mode='raw', doc=doc)
        js = """
        function openInNewTab(url) {
        var win = window.open(url, '_blank');
        win.focus();
        }
        setTimeout(function(){ openInNewTab('http://localhost:5006/grabcut') }, 250);
        """
        callback = CustomJS(code=js)
        for button in widgets.select({"type":Button}):
            button.js_on_click(callback)
        return widgets



class GrabCutButton(param.Parameterized):
    """
    Button to run the grab cut algorithm with the selected bounding box
    """

    extract = param.Action(precedence=0.01)

    def __init__(self, select_region, **params):
        super(GrabCutButton, self).__init__(**params)
        self.params('extract').default = self.load_data
        self.select_region = select_region


    def load_data(self, obj, **kwargs):
        shared_state.set_state(bbox=self.select_region.plot.get_bbox())
        shared_state.set_state(zoom_level=self.select_region.plot.zoom_level)




class SelectRegion(DashboardLayout):
    """
    Dashboard to select a region of the Earth on which to apply the grab
    cut algorithm.
    """

    def __init__(self):
        self.plot = SelectRegionPlot()

    def __call__(self, shared_state, doc):
        return self.model(self.plot(), doc)


class GrabCutsLayout(DashboardLayout):
    """
    Layout that shows the grab cut visualization.
    """

    def __init__(self, tiff_file, bbox, **params):
        super(GrabCutsLayout, self).__init__(**params)
        arr = xr.open_rasterio(tiff_file)

        # Originally crs of RGB was specified as ccrs.UTM(18)
        rgb = gv.RGB((arr.x, arr.y, arr[0].values,
                      arr[1].values, arr[2].values),
                     vdims=['R', 'G', 'B'])
        self.dashboard = GrabCutDashboard(rgb, fg_data=[], bg_data=[], height=600,
                                          name='GrabCut Extractor')

    @classmethod
    def tiff_from_bbox(cls, tile_server, zoom_level, bbox):
        options = {'tile_server': tile_server, 'zoom_level': zoom_level,
                   'bbox': bbox, 'crop_to_bbox':True}

        quest_service = 'svc://wmts:seamless_imagery'
        tile_service_options = quest.api.download_options(quest_service,
                                                          fmt='param')[quest_service]
        basemap_features = quest.api.get_features(quest_service)
        collection_name = 'examples'
        if collection_name in quest.api.get_collections():
            pass
        else:
            quest.api.new_collection(collection_name)

        collection_feature = quest.api.add_features(collection_name, basemap_features[0])

        staged_id = quest.api.stage_for_download(collection_feature, options=options)
        download_state = quest.api.download_datasets(staged_id)
        # Fragile, needs improvement
        download_id = list(download_state.keys())[0]

        meta = quest.api.get_metadata(staged_id)
        file_path = meta[download_id].get('file_path',None)
        if not os.path.isfile(file_path):
            print('Error: No TIFF downloaded')
        return file_path

    def __call__(self, shared_state, doc):
        return self.model(self.dashboard.view(), doc)


class GrabCutSettings(DashboardLayout):
    """
    Layout showing the grabcut visualization widgets.
    """

    def __init__(self, grabcut, **params):
        super(GrabCutSettings, self).__init__(**params)
        self.grabcut = grabcut

    def __call__(self, shared_state, doc):
        return parambokeh.Widgets(self.grabcut.dashboard, mode='raw', doc=doc)



class SelectRegionApp(param.Parameterized, App):
    """
    The region selection dashboard.
    """

    def __init__(self, **params):
        super(SelectRegionApp, self).__init__(**params)
        self.load_theme()
        self.layouts = {}

        self.instructions = "<div style='text-align:left'>In this dashboard you can select the BoxEdit tool and double click to define the start and end of the region of interest. The magnification determines how the resolution will scale up relative to the chosen selection. </div>"

    def viewable(self, doc=None):
        self.apply_theming(doc)

        select_region = SelectRegion()
        widgets = SelectRegionWidgets(select_region)

        self.layouts[doc] = ColumnLayouts(
            [DivLayout(self.instructions, width=1300),
            ComposeLayouts([[LaunchGrabCut(select_region), DivLayout('', width=900)],
                            [widgets, select_region]
                ])
             ]
        )



        return self.layouts[doc](shared_state, doc)


class GrabCutApp(param.Parameterized, App):
    """
    The grab cut dashboard
    """

    def __init__(self, **params):
        super(GrabCutApp, self).__init__(**params)
        self.load_theme()
        self.layouts = {}

        self.instructions = "<div style='text-align:left'>In this dashboard you can apply the grabcut algorithm to extract a coastline by drawing the foreground and background with the freehand draw tool. You can also filter out small undesired features by size. </div>"

    def viewable(self, doc=None):
        self.apply_theming(doc)

        tile_server = shared_state.state.get('tile_server', None)
        bbox = shared_state.state.get('bbox', None)
        zoom_level = shared_state.state.get('zoom_level', None)
        if None in [tile_server, bbox, zoom_level]:
            print('Missing information for selecting a tile.')

        grabcut = GrabCutsLayout(GrabCutsLayout.tiff_from_bbox(tile_server, zoom_level, bbox), bbox)
        grabcutsettings = GrabCutSettings(grabcut)
        self.layouts[doc] = ColumnLayouts(
            [DivLayout(self.instructions, width=1300),
             ComposeLayouts([[grabcutsettings, grabcut]])])
        return self.layouts[doc](shared_state, doc)
