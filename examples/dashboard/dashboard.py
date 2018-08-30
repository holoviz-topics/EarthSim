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
from earthsim.grabcut import GrabCutDashboard


misc_servers =  ['http://c.tile.openstreetmap.org/{Z}/{X}/{Y}.png',
                 'https://s.basemaps.cartocdn.com/light_all/{Z}/{X}/{Y}.png',
                 'http://tile.stamen.com/terrain/{Z}/{X}/{Y}.png']

arcgis_server = 'https://server.arcgisonline.com/ArcGIS/rest/services/'
arcgis_paths = ['World_Imagery/MapServer/tile/{Z}/{Y}/{X}',
                'World_Topo_Map/MapServer/tile/{Z}/{Y}/{X}',
                'World_Terrain_Base/MapServer/tile/{Z}/{Y}/{X}',
                'World_Street_Map/MapServer/tile/{Z}/{Y}/{X}',
                'World_Shaded_Relief/MapServer/tile/{Z}/{Y}/{X}',
                'World_Physical_Map/MapServer/tile/{Z}/{Y}/{X}',
                'USA_Topo_Maps/MapServer/tile/{Z}/{Y}/{X}',
                'Ocean_Basemap/MapServer/tile/{Z}/{Y}/{X}',
                'NatGeo_World_Map/MapServer/tile/{Z}/{Y}/{X}']
arcgis_urls = [arcgis_server + arcgis_path for arcgis_path in arcgis_paths]
URL_LIST = arcgis_urls + misc_servers



class SelectRegionWidgets(DashboardLayout):
    """
    Provides the Bokeh widgets for the region selection dashboard
    """

    def __init__(self, layout):
        self.layout = layout
        shared_state.set_state(url=self.layout.plot.url)

    def callback(self, obj, **kwargs):
        self.layout.plot.set_url(obj.url)
        shared_state.set_state(url=obj.url)


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


class SelectRegionPlot(param.Parameterized):
    """
    Visualization that allows selecting a bounding box anywhere on a tile source.
    """

    name = param.String(default='Region Settings')


    url = param.ObjectSelector(default=URL_LIST[0], objects=URL_LIST)
    width = param.Integer(default=900, precedence=-1, doc="Width of the plot in pixels")

    height = param.Integer(default=700, precedence=-1, doc="Height of the plot in pixels")


    zoom_level = param.Integer(default=7, bounds=(1,21), precedence=-1, doc="""
       The zoom level is updated when the bounding box is drawn."""   )

    def __init__(self, **params):
        super(SelectRegionPlot, self).__init__(**params)
        self.url_stream = hv.streams.Stream.define('url', url=self.url)()
        self.box_stream = None

    @classmethod
    def bounds_to_zoom_level(cls, bounds, width, height,
                             tile_width=256, tile_height=256, max_zoom=21):
        """
        Computes the zoom level from the lat/lon bounds and the plot width and height

        bounds: tuple(float)
            Bounds in the form (lon_min, lat_min, lon_max, lat_max)
        width: int
            Width of the overall plot
        height: int
            Height of the overall plot
        tile_width: int (default=256)
            Width of each tile
        tile_width: int (default=256)
            Height of each tile
        max_zoom: int (default=21)
            Maximum allowed zoom level
        """

        def latRad(lat):
            sin = math.sin(lat * math.pi / 180);
            if sin == 1:
                radX2 = 20
            else:
                radX2 = math.log((1 + sin) / (1 - sin)) / 2;
            return max(min(radX2, math.pi), -math.pi) / 2;

        def zoom(mapPx, worldPx, fraction):
            return math.floor(math.log(mapPx / worldPx / fraction) / math.log(2));

        x0, y0, x1, y1 = bounds
        latFraction = (latRad(y1) - latRad(y0)) / math.pi
        lngDiff = x1 - x0
        lngFraction = ((lngDiff + 360) if lngDiff < 0 else lngDiff)/360
        latZoom = zoom(height, tile_height, latFraction)
        lngZoom = zoom(width, tile_width, lngFraction)
        return min(latZoom, lngZoom, max_zoom)


    def set_url(self, url):
        self.url = url
        self.url_stream.event(url=url)

    def callback(self, url):
        return (gv.WMTS(url, extents=(-180, -90, 180, 90),
                        crs=ccrs.PlateCarree()).options(width=500, height=500) *
                gv.WMTS(gv.tile_sources.StamenLabels.data,
                        extents=(-180, -90, 180, 90),
                        crs=ccrs.PlateCarree()).options(width=500, height=500))


    def get_bbox(self):
        element = self.box_stream.element
        # Update shared_state with bounding box (if any)
        if element:
            xs, ys = element.array().T
            bbox = (xs[0], ys[0], xs[2], ys[1])
            # Set the zoom level
            zoom_level = self.bounds_to_zoom_level(bbox, self.width, self.height)
            self.zoom_level = zoom_level
            return bbox
        else:
            return None


    def __call__(self):
        tiles = gv.DynamicMap(self.callback, streams=[self.url_stream])
        boxes = gv.Polygons([], crs=ccrs.PlateCarree()).options(fill_alpha=0.5,
                                                                color='grey',
                                                                line_color='white',
                                                                line_width=2)
        self.box_stream = hv.streams.BoxEdit(source=boxes,num_objects=1)
        return (tiles * boxes).options(width=self.width, height=self.height)

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
    def tiff_from_bbox(cls, url, zoom_level, bbox):
        options = {'url': url, 'zoom_level': zoom_level,
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

        url = shared_state.state.get('url', None)
        bbox = shared_state.state.get('bbox', None)
        zoom_level = shared_state.state.get('zoom_level', None)
        if None in [url, bbox, zoom_level]:
            print('Missing information for selecting a tile.')

        grabcut = GrabCutsLayout(GrabCutsLayout.tiff_from_bbox(url, zoom_level, bbox), bbox)
        grabcutsettings = GrabCutSettings(grabcut)
        self.layouts[doc] = ColumnLayouts(
            [DivLayout(self.instructions, width=1300),
             ComposeLayouts([[grabcutsettings, grabcut]])])
        return self.layouts[doc](shared_state, doc)
