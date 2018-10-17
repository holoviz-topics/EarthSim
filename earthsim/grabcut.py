import os
import math
import warnings

import param
import numpy as np
import holoviews as hv
import geoviews as gv
import cartopy.crs as ccrs
import datashader as ds
import quest

from PIL import Image, ImageDraw
from holoviews.core.operation import Operation
from holoviews.core.options import Store, Options
from holoviews.core.util import pd
from holoviews.element.util import split_path
from holoviews.operation.datashader import ResamplingOperation, rasterize, regrid
from holoviews.operation import contours
from holoviews.streams import Stream, FreehandDraw, Params, BoxEdit, ParamMethod


class rasterize_polygon(ResamplingOperation):
    """
    Rasterizes Polygons elements to a boolean mask using PIL
    """

    def _process(self, element, key=None):
        sampling = self._get_sampling(element, 0, 1)
        (x_range, y_range), (xvals, yvals), (width, height), (xtype, ytype) = sampling
        (x0, x1), (y0, y1) = x_range, y_range
        img = Image.new('L', (width, height), 0)
        draw = ImageDraw.Draw(img)
        for poly in element.split():
            poly = poly.reindex(vdims=[])
            for p in split_path(poly):
                xs, ys = (p.values if pd else p).T
                xs = ((xs - x0) / (x1-x0) * width)
                ys = ((ys - y0) / (y1-y0) * height)
                draw.polygon(list(zip(xs, ys)), outline=1, fill=1)
        img = np.array(img).astype('bool')
        return hv.Image((xvals, yvals, img), element.kdims)


class extract_foreground(Operation):
    """
    Uses Grabcut algorithm to extract the foreground from an image given
    path or polygon types.
    """

    foreground = param.ClassSelector(class_=hv.Path)

    background = param.ClassSelector(class_=hv.Path)

    iterations = param.Integer(default=5, bounds=(0, 20), doc="""
        Number of iterations to run the GrabCut algorithm for.""")

    def _process(self, element, key=None):
        try:
            import cv2 as cv
        except ImportError:
            raise ImportError('GrabCut algorithm requires openCV')

        if isinstance(self.p.foreground, hv.Polygons):
            rasterize_op = rasterize_polygon
        else:
            rasterize_op = rasterize.instance(aggregator=ds.any())

        kwargs = {'dynamic': False, 'target': element}
        fg_mask = rasterize_op(self.p.foreground, **kwargs)
        bg_mask = rasterize_op(self.p.background, **kwargs)
        fg_mask = fg_mask.dimension_values(2, flat=False)
        bg_mask = bg_mask.dimension_values(2, flat=False)
        if fg_mask[np.isfinite(fg_mask)].sum() == 0 or bg_mask[np.isfinite(bg_mask)].sum() == 0:
            return element.clone([], vdims=['Foreground'], new_type=gv.Image,
                                 crs=element.crs)

        mask = np.where(fg_mask, 1, 2)
        mask = np.where(bg_mask, 0, mask).copy()
        bgdModel = np.zeros((1,65), np.float64)
        fgdModel = np.zeros((1,65), np.float64)

        if isinstance(element, hv.RGB):
            img = np.dstack([element.dimension_values(d, flat=False)
                             for d in element.vdims])
        else:
            img = element.dimension_values(2, flat=False)
        mask, _, _ = cv.grabCut(img, mask.astype('uint8'), None, bgdModel, fgdModel,
                                self.p.iterations, cv.GC_INIT_WITH_MASK)
        fg_mask = np.where((mask==2)|(mask==0),0,1).astype('bool')
        xs, ys = (element.dimension_values(d, expanded=False) for d in element.kdims)
        return element.clone((xs, ys, fg_mask), vdims=['Foreground'], new_type=gv.Image,
                             crs=element.crs)


class filter_polygons(Operation):

    minimum_size = param.Integer(default=10)

    link_inputs = param.Boolean(default=True)

    def _process(self, element, key=None):
        paths = []
        for path in element.split():
            if len(path) < self.p.minimum_size:
                continue
            for p in split_path(path):
                if len(p) > self.p.minimum_size:
                    paths.append(p)
        return element.clone(paths)


class GrabCutPanel(param.Parameterized):
    """
    Defines a Panel for extracting contours from an Image.
    """

    crs = param.ClassSelector(default=ccrs.PlateCarree(), class_=ccrs.Projection,
                              precedence=-1, doc="""
        Projection the inputs and output paths are defined in.""")

    path_type = param.ClassSelector(default=gv.Path, class_=hv.Path,
                                    precedence=-1, is_instance=False, doc="""
        The element type to draw into.""")

    update_contour = param.Action(default=lambda o: o.param.trigger('update_contour'),
                                  precedence=1, doc="""
        Button triggering GrabCut.""")

    filter_contour = param.Action(default=lambda o: o._trigger_filter(),
                                  precedence=1, doc="""
        Button triggering filtering of contours.""")

    width = param.Integer(default=500, precedence=-1, doc="""
        Width of the plot""")

    height = param.Integer(default=None, precedence=-1, doc="""
        Height of the plot""")

    downsample = param.Magnitude(default=1., doc="""
        Amount to downsample image by before applying grabcut.""")

    iterations = param.Integer(default=5, bounds=(0, 20), doc="""
        Number of iterations to run the GrabCut algorithm for.""")

    minimum_size = param.Integer(default=10)

    def __init__(self, image, fg_data=[], bg_data=[], **params):
        self.image = image
        super(GrabCutPanel, self).__init__(**params)
        self.bg_paths = gv.project(self.path_type(bg_data, crs=self.crs), projection=image.crs)
        self.fg_paths = gv.project(self.path_type(fg_data, crs=self.crs), projection=image.crs)
        self.draw_bg = FreehandDraw(source=self.bg_paths)
        self.draw_fg = FreehandDraw(source=self.fg_paths)
        self._initialized = False
        self._filter = False

    @param.depends('update_contour')
    def extract_foreground(self, **kwargs):
        img = self.image
        if self._initialized:
            bg, fg = self.draw_bg.element, self.draw_fg.element
        else:
            self._initialized = True
            bg, fg = self.bg_paths, self.fg_paths
        bg, fg = (gv.project(g, projection=img.crs) for g in (bg, fg))

        if not len(bg) or not len(fg):
            return gv.Path([], img.kdims, crs=img.crs)

        if self.downsample != 1:
            kwargs = {'dynamic': False}
            h, w = img.interface.shape(img, gridded=True)
            kwargs['width'] = int(w*self.downsample)
            kwargs['height'] = int(h*self.downsample)
            img = regrid(img, **kwargs)

        foreground = extract_foreground(img, background=bg, foreground=fg,
                                        iterations=self.iterations)
        foreground = gv.Path([contours(foreground, filled=True, levels=1).split()[0].data],
                             kdims=foreground.kdims, crs=foreground.crs)
        self.result = gv.project(foreground, projection=self.crs)
        return foreground

    def _trigger_filter(self):
        self._filter = True
        self.param.trigger('filter_contour')
        self._filter = False

    @param.depends('filter_contour')
    def _filter_contours(self, obj, **kwargs):
        if self._filter:
            obj = filter_polygons(obj, minimum_size=self.minimum_size)
        self.result = gv.project(obj, projection=self.crs)
        return obj

    def view(self):
        height = self.height
        if height is None:
            h, w = self.image.dimension_values(2, flat=False).shape[:2]
            height = int(self.width*(h/w))
        options = dict(width=self.width, height=height, xaxis=None, yaxis=None,
                       projection=self.image.crs)
        dmap = hv.DynamicMap(self.extract_foreground)
        dmap = hv.util.Dynamic(dmap, operation=self._filter_contours)
        return (regrid(self.image).options(**options) * self.bg_paths * self.fg_paths +
                dmap.options(**options))



class SelectRegionPanel(param.Parameterized):
    """
    Visualization that allows selecting a bounding box anywhere on a tile source.
    """

    # Tile servers
    misc_servers =  {'OpenStreetMap' : 'http://c.tile.openstreetmap.org/{Z}/{X}/{Y}.png',
                     'Basemaps CartoCDN' :
                     'https://s.basemaps.cartocdn.com/light_all/{Z}/{X}/{Y}.png',
                     'Stamen':'http://tile.stamen.com/terrain/{Z}/{X}/{Y}.png'}

    arcgis_paths = {'World Imagery':'World_Imagery/MapServer/tile/{Z}/{Y}/{X}',
                    'World Topo Map':'World_Topo_Map/MapServer/tile/{Z}/{Y}/{X}',
                    'World Terrain Base':'World_Terrain_Base/MapServer/tile/{Z}/{Y}/{X}',
                    'World Street Map': 'World_Street_Map/MapServer/tile/{Z}/{Y}/{X}',
                    'World Shaded Relief': 'World_Shaded_Relief/MapServer/tile/{Z}/{Y}/{X}',
                    'World Physical Map': 'World_Physical_Map/MapServer/tile/{Z}/{Y}/{X}',
                    'USA Topo Maps' : 'USA_Topo_Maps/MapServer/tile/{Z}/{Y}/{X}',
                    'Ocean Basemap' : 'Ocean_Basemap/MapServer/tile/{Z}/{Y}/{X}',
                    'NatGeo World Map' : 'NatGeo_World_Map/MapServer/tile/{Z}/{Y}/{X}'}

    arcgis_urls = {k: 'https://server.arcgisonline.com/ArcGIS/rest/services/' + v
                   for k,v in arcgis_paths.items()}

    tile_urls = dict(misc_servers, **arcgis_urls)

    # Parameters
    name = param.String(default='Region Settings')

    width = param.Integer(default=900, precedence=-1, doc="Width of the plot in pixels")

    height = param.Integer(default=700, precedence=-1, doc="Height of the plot in pixels")

    zoom_level = param.Integer(default=7, bounds=(1,21), precedence=-1, doc="""
       The zoom level is updated when the bounding box is drawn."""   )

    tile_server = param.ObjectSelector(default=tile_urls['World Imagery'], objects=tile_urls)

    magnification = param.Integer(default=1, bounds=(1,10), precedence=0.1)

    def __init__(self, poly_data=[], **params):
        super(SelectRegionPanel, self).__init__(**params)
        self.boxes = gv.Polygons(poly_data).options(
            fill_alpha=0.5, color='grey', line_color='white',
            line_width=2, width=self.width, height=self.height
        )
        self.box_stream = BoxEdit(source=self.boxes, num_objects=1)

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

    @param.depends('tile_server')
    def callback(self):
        return (gv.WMTS(self.tile_server) * gv.tile_sources.StamenLabels())

    @property
    def bbox(self):
        element = self.box_stream.element if self.box_stream.data else self.boxes
        # Update shared_state with bounding box (if any)
        if element:
            xs, ys = element.array().T
            bbox = (xs[0], ys[0], xs[2], ys[1])
            # Set the zoom level
            zoom_level = self.bounds_to_zoom_level(bbox, self.width, self.height)
            self.zoom_level = zoom_level + self.magnification
            return bbox
        else:
            return None

    def view(self):
        return (gv.DynamicMap(self.callback) * self.boxes)

    def get_tiff(self):
        bbox = self.bbox
        filepath = self.tiff_from_bbox(self.tile_server, self.zoom_level, bbox)
        return gv.load_tiff(filepath, crs=ccrs.PlateCarree()).redim(x='Longitude', y='Latitude')

    @classmethod
    def tiff_from_bbox(cls, tile_server, zoom_level, bbox):
        if bbox is None:
            raise ValueError('Please supply a bounding box in order to extract a tiff.')

        options = {'url': tile_server, 'zoom_level': zoom_level,
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


options = Store.options('bokeh')

options.Points = Options('plot', padding=0.1)
options.Path = Options('plot', padding=0.1)
options.Polygons = Options('plot', padding=0.1)
