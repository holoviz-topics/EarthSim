"""
PyViz-based tools for interactively creating plots dynamically from other plots.
"""

from collections import Callable, Iterable

import param
import numpy as np
import datashader as ds
import holoviews as hv
import geoviews as gv
import cartopy.crs as ccrs

from geoviews import Points, WMTS, Path
from holoviews.streams import PolyDraw, PolyEdit, PointerX
from holoviews import Curve, NdOverlay, DynamicMap, VLine, Image, TriMesh
from holoviews.operation.datashader import datashade, rasterize
from holoviews.util import Dynamic


class LineCrossSection(param.Parameterized):
    """
    LineCrossSection rasterizes any HoloViews element and takes
    cross-sections of the resulting Image along poly-lines drawn
    using the PolyDraw tool.
    """

    aggregator = param.ClassSelector(class_=ds.reductions.Reduction,
                                     default=ds.mean())

    tile_url = param.String(default='http://c.tile.openstreetmap.org/{Z}/{X}/{Y}.png',
                            doc="URL for the tile source", precedence=-1)

    resolution = param.Number(default=1000, doc="""
        Distance between samples in meters. Used for interpolation
        of the cross-section paths.""")

    def __init__(self, obj, **params):
        super(LineCrossSection, self).__init__(**params)
        self.obj = obj
        self.path = Path([])
        self.path_stream = PolyDraw(source=self.path)
        PolyEdit(source=self.path)
        self.sections = Dynamic(self.obj, operation=self._sample,
                                streams=[self.path_stream])
        self.tiles = WMTS(self.tile_url)


    def _gen_samples(self, geom):
        """
        Interpolates a LineString geometry to the defined
        resolution. Returning the x- and y-coordinates along
        with the distance along the path.
        """
        xs, ys, distance = [], [], []
        dist = geom.length
        for d in np.linspace(0, dist, int(dist/self.resolution)):
            point = geom.interpolate(d)
            xs.append(point.x)
            ys.append(point.y)
            distance.append(d)
        return xs, ys, distance


    def _sample(self, obj, data):
        """
        Rasterizes the supplied object in the current region
        and samples it with the drawn paths returning an
        NdOverlay of Curves.

        Note: Because the function returns an NdOverlay containing
        a variable number of elements batching must be enabled and
        the legend_limit must be set to 0.
        """
        path = self.path_stream.element
        if isinstance(obj, TriMesh): 
            vdim = obj.nodes.vdims[0]
        else:
            vdim = obj.vdims[0]
        if len(path) > 2:
            x_range = path.range(0)
            y_range = path.range(1)
        else:
            return NdOverlay({0: Curve([], 'Distance', vdim)})

        (x0, x1), (y0, y1) = x_range, y_range
        width, height = (max([min([(x1-x0)/self.resolution, 500]), 10]),
                         max([min([(y1-y0)/self.resolution, 500]), 10]))
        raster = rasterize(obj, x_range=x_range, y_range=y_range,
                           aggregator=self.aggregator, width=int(width),
                           height=int(height), dynamic=False)
        x, y = raster.kdims
        sections = []
        for g in path.geom():
            xs, ys, distance = self._gen_samples(g)
            indexes = {x.name: xs, y.name: ys}
            points = raster.data.sel_points(method='nearest', **indexes).to_dataframe()
            points['Distance'] = distance
            sections.append(Curve(points, 'Distance', vdims=[vdim, x, y]))
        return NdOverlay(dict(enumerate(sections)))


    def _pos_indicator(self, obj, x):
        """
        Returns an NdOverlay of Points indicating the current
        mouse position along the cross-sections.

        Note: Because the function returns an NdOverlay containing
        a variable number of elements batching must be enabled and
        the legend_limit must be set to 0.
        """
        points = []
        elements = obj or []
        for el in elements:
            if len(el)<1:
                continue
            p = Points(el[x], ['x', 'y'], crs=ccrs.GOOGLE_MERCATOR)
            points.append(p)
        if not points:
            return NdOverlay({0: Points([], ['x', 'y'])})
        return NdOverlay(enumerate(points))


    def view(self, cmap=None, shade=True):
        raster_opts = dict(aggregator=self.aggregator, precompute=True)
        cmap_opts = dict(cmap=cmap) if cmap else {}
        if shade:
            if cmap: raster_opts.update(cmap_opts)
            shaded = datashade(self.obj, **raster_opts)
        else:
            shaded = rasterize(self.obj, **raster_opts).opts(style=cmap_opts)
        point_x = PointerX(source=self.sections, x=0)
        vline = DynamicMap(VLine, streams=[point_x])
        points = Dynamic(self.sections, operation=self._pos_indicator,
                         streams=[point_x])
        return (self.tiles * shaded * self.path * points +
                self.sections * vline)


    
class SurfaceCrossSection(LineCrossSection):
    """
    SurfaceCrossSection rasterizes the input data, which should be a
    HoloMap or DynamicMap indexed by time and takes cross-sections of
    the resulting stack of images along paths drawn using a PolyDraw
    tool.
    """

    def _sample(self, obj, data):
        """
        Rasterizes the supplied object across times returning
        an Image of the sampled data across time and distance.
        """
        path = self.path_stream.element
        if isinstance(obj, TriMesh): 
            vdim = obj.nodes.vdims[0]
        else:
            vdim = obj.vdims[0]

        if len(path) > 2:
            x_range = path.range(0)
            y_range = path.range(1)
        else:
            return Image([], ['Distance', 'Time'], vdim.name)

        g= path.geom()[-1]
        xs, ys, distance = self._gen_samples(g)
        sections = []

        if isinstance(self.obj, DynamicMap):
            times = self.obj.kdims[0].values
        else:
            times = self.obj.keys()

        (x0, x1), (y0, y1) = x_range, y_range
        width, height = (max([min([(x1-x0)/self.resolution, 500]), 10]),
                         max([min([(y1-y0)/self.resolution, 500]), 10]))
        for t in times:
            raster = rasterize(self.obj[t], x_range=x_range, y_range=y_range,
                               aggregator=self.aggregator, width=int(width),
                               height=int(height), dynamic=False)
            x, y = raster.kdims
            indexes = {x.name: xs, y.name: ys}
            points = raster.data.sel_points(method='nearest', **indexes).to_dataframe()
            sections.append(points[vdim.name])
        return Image((distance, times, np.vstack(sections)), ['Distance', self.obj.kdims[0]], vdim)


    def view(self, cmap=None, shade=True):
        raster_opts = dict(aggregator=self.aggregator, precompute=True)
        cmap_opts = dict(cmap=cmap) if cmap else {}
        if shade:
            if cmap: raster_opts.update(cmap_opts)
            shaded = datashade(self.obj, **raster_opts)
        else:
            shaded = rasterize(self.obj, **raster_opts).opts(style=cmap_opts)
        return self.tiles * shaded * self.path + self.sections
