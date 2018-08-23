import warnings

import param
import numpy as np
import holoviews as hv
import geoviews as gv
import cartopy.crs as ccrs
import datashader as ds

from PIL import Image, ImageDraw
from holoviews.core.operation import Operation
from holoviews.core.util import pd
from holoviews.element.util import split_path
from holoviews.operation.datashader import ResamplingOperation, rasterize, regrid
from holoviews.operation import contours
from holoviews.streams import Stream, FreehandDraw


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

        mask = np.where(fg_mask, fg_mask, 2)
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

    def _process(self, element, key=None):
        paths = []
        for path in element.split():
            if len(path) < self.p.minimum_size:
                continue
            for p in split_path(path):
                if len(p) > self.p.minimum_size:
                    paths.append(p)
        return element.clone(paths)



class GrabCutDashboard(Stream):
    """
    Defines a Dashboard for extracting contours from an Image.
    """

    crs = param.ClassSelector(default=ccrs.PlateCarree(), class_=ccrs.Projection,
                              precedence=-1, doc="""
        Projection the inputs and output paths are defined in.""")

    path_type = param.ClassSelector(default=gv.Path, class_=hv.Path,
                                    precedence=-1, is_instance=False, doc="""
        The element type to draw into.""")

    update_contour = param.Action(default=lambda self: self.event(), precedence=1,
                               doc="""Button triggering GrabCut.""")

    filter_contour = param.Action(default=lambda self: self.filter_stream.event(filter=True), precedence=1,
                                  doc="""Button triggering GrabCut.""")

    width = param.Integer(default=600, precedence=-1, doc="""
        Width of the plot""")

    height = param.Integer(default=600, precedence=-1, doc="""
        Height of the plot""")

    downsample = param.Magnitude(default=1., doc="""
        Amount to downsample image by before applying grabcut.""")

    iterations = param.Integer(default=5, bounds=(0, 20), doc="""
        Number of iterations to run the GrabCut algorithm for.""")

    minimum_size = param.Integer(default=10)

    def __init__(self, image, fg_data=[], bg_data=[], **params):
        self.image = image
        super(GrabCutDashboard, self).__init__(transient=True, **params)
        self.bg_paths = gv.project(self.path_type(bg_data, crs=self.crs), projection=image.crs)
        self.fg_paths = gv.project(self.path_type(fg_data, crs=self.crs), projection=image.crs)
        self.draw_bg = FreehandDraw(source=self.bg_paths)
        self.draw_fg = FreehandDraw(source=self.fg_paths)
        self.filter_stream = hv.streams.Stream.define('Filter', filter=False)(transient=True)
        self._initialized = False
        self._filter = False

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

        foreground = extract_foreground(img, background=bg, foreground=fg, iterations=self.iterations)
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore')
            foreground = gv.Path([contours(foreground, filled=True, levels=1).split()[0].data],
                                 kdims=foreground.kdims, crs=foreground.crs)
        self.result = gv.project(foreground, projection=self.crs)
        return foreground

    def filter_contours(self, obj, **kwargs):
        if kwargs.get('filter'):
            obj = filter_polygons(obj, minimum_size=self.minimum_size)
        self.result = obj
        return obj

    def view(self):
        # TODO: Removed projection=self.image.crs to overlay on tile source
        options = dict(width=self.width, height=self.height, xaxis=None, yaxis=None)
        dmap = hv.DynamicMap(self.extract_foreground, streams=[self])
        dmap = hv.util.Dynamic(dmap, operation=self.filter_contours,
                               streams=[self.filter_stream])
        return (gv.tile_sources.Wikipedia * regrid(self.image).options(**options)
                * self.bg_paths * self.fg_paths +
                dmap.options(**dict(tools=['tap'], **options))).options(merge_tools=False, clone=False)
