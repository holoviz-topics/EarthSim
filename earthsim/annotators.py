"""
Helper functions for building interactive plots that support persistent user annotations.
"""

from functools import partial

import param
import numpy as np
import pandas as pd
import panel as pn
import cartopy.crs as ccrs
import geopandas as gpd
import holoviews as hv
import geoviews as gv
import holoviews.plotting.bokeh

from holoviews import DynamicMap, Path, Table, NdOverlay, Store, Options
from holoviews.core.util import disable_constant
from holoviews.plotting.links import DataLink
from holoviews.streams import Selection1D, Stream, PolyDraw, PolyEdit, PointDraw, CDSStream
from geoviews.data.geopandas import GeoPandasInterface
from geoviews import Polygons, Points, WMTS, TriMesh, Path as GeoPath
from geoviews.util import path_to_geom_dicts
from shapely.geometry import Polygon, LinearRing, MultiPolygon

from .models.custom_tools import CheckpointTool, RestoreTool, ClearTool
from .links import VertexTableLink, PointTableLink


def paths_to_polys(path):
    """
    Converts a Path object to a Polygons object by extracting all paths
    interpreting inclusion zones as holes and then constructing Polygon
    and MultiPolygon geometries for each path.
    """
    geoms = path_to_geom_dicts(path)

    polys = []
    for geom in geoms:
        g = geom['geometry']
        found = False
        for p in list(polys):
            if Polygon(p['geometry']).contains(g):
                if 'holes' not in p:
                    p['holes'] = []
                p['holes'].append(g)
                found = True
            elif Polygon(g).contains(p['geometry']):
                polys.pop(polys.index(p))
                if 'holes' not in geom:
                    geom['holes'] = []
                geom['holes'].append(p['geometry'])
        if not found:
            polys.append(geom)

    polys_with_holes = []
    for p in polys:
        geom = p['geometry']
        holes = []
        if 'holes' in p:
            holes = [LinearRing(h) for h in p['holes']]

        if 'Multi' in geom.type:
            polys = []
            for g in geom:
                subholes = [h for h in holes if g.intersects(h)]
                polys.append(Polygon(g, subholes))
            poly = MultiPolygon(polys)
        else:
            poly = Polygon(geom, holes)
        p['geometry'] = poly
        polys_with_holes.append(p)
    return path.clone(polys_with_holes, new_type=gv.Polygons)


def poly_to_geopandas(polys, columns):
    """
    Converts a GeoViews Paths or Polygons type to a geopandas dataframe.

    Parameters
    ----------

    polys : gv.Path or gv.Polygons
        GeoViews element
    columns: list(str)
        List of columns

    Returns
    -------
    gdf : Geopandas dataframe
    """
    rows = []
    for g in polys.geom():
        rows.append(dict({c: '' for c in columns}, geometry=g))
    return gpd.GeoDataFrame(rows, columns=columns+['geometry'])


def initialize_tools(plot, element):
    """
    Initializes the Checkpoint and Restore tools.
    """
    cds = plot.handles['source']
    checkpoint = plot.state.select(type=CheckpointTool)
    restore = plot.state.select(type=RestoreTool)
    clear = plot.state.select(type=ClearTool)
    if checkpoint:
        checkpoint[0].sources.append(cds)
    if restore:
        restore[0].sources.append(cds)
    if clear:
        clear[0].sources.append(cds)


def preprocess(function, current=[]):
    """
    Turns a param.depends watch call into a preprocessor method, i.e.
    skips all downstream events triggered by it.

    NOTE: This is a temporary hack while the addition of preprocessors
          in param is under discussion. This only works for the first
          method which depends on a particular parameter.

          (see https://github.com/pyviz/param/issues/332)
    """
    def inner(*args, **kwargs):
        self = args[0]
        self.param._BATCH_WATCH = True
        function(*args, **kwargs)
        self.param._BATCH_WATCH = False
        self.param._watchers = []
        self.param._events = []
    return inner


class GeoAnnotator(param.Parameterized):
    """
    Provides support for drawing polygons and points on top of a map.
    """

    tile_url = param.String(default='http://c.tile.openstreetmap.org/{Z}/{X}/{Y}.png',
                            doc="URL for the tile source", precedence=-1)

    extent = param.NumericTuple(default=(np.nan,)*4, doc="""
         Initial extent if no data is provided.""", precedence=-1)

    path_type = param.ClassSelector(default=Polygons, class_=Path, is_instance=False, doc="""
         The element type to draw into.""")

    polys = param.ClassSelector(class_=Path, precedence=-1, doc="""
         Polygon or Path element to annotate""")

    points = param.ClassSelector(class_=Points, precedence=-1, doc="""
         Point element to annotate""")

    height = param.Integer(default=500, doc="Height of the plot",
                           precedence=-1)

    width = param.Integer(default=900, doc="Width of the plot",
                          precedence=-1)

    def __init__(self, polys=None, points=None, crs=None, **params):
        super(GeoAnnotator, self).__init__(**params)
        plot_opts = dict(height=self.height, width=self.width)
        self.tiles = WMTS(self.tile_url, extents=self.extent,
                          crs=ccrs.PlateCarree()).opts(plot=plot_opts)
        polys = [] if polys is None else polys
        points = [] if points is None else points
        crs = ccrs.GOOGLE_MERCATOR if crs is None else crs
        self._tools = [CheckpointTool(), RestoreTool(), ClearTool()]
        if not isinstance(polys, Path):
            polys = self.path_type(polys, crs=crs)
        self._init_polys(polys)
        if not isinstance(points, Points):
            points = Points(points, self.polys.kdims, crs=crs)
        self._init_points(points)

    @param.depends('polys', watch=True)
    @preprocess
    def _init_polys(self, polys=None):
        opts = dict(tools=self._tools, finalize_hooks=[initialize_tools], color_index=None)
        polys = self.polys if polys is None else polys
        self.polys = polys.options(**opts)
        self.poly_stream = PolyDraw(source=self.polys, data={}, show_vertices=True)
        self.vertex_stream = PolyEdit(source=self.polys, vertex_style={'nonselection_alpha': 0.5})

    @param.depends('points', watch=True)
    @preprocess
    def _init_points(self, points=None):
        opts = dict(tools=self._tools, finalize_hooks=[initialize_tools], color_index=None)
        points = self.points if points is None else points
        self.points = points.options(**opts)
        self.point_stream = PointDraw(source=self.points, drag=True, data={})

    def pprint(self):
        params = dict(self.get_param_values())
        name = params.pop('name')
        string = '%s\n%s\n\n' % (name, '-'*len(name))
        for item in sorted(params.items()):
            string += '  %s: %s\n' % (item)
        print(string)

    @param.depends('points', 'polys')
    def map_view(self):
        return self.tiles * self.polys * self.points

    def panel(self):
        return pn.Row(self.map_view)


class PointWidgetAnnotator(GeoAnnotator):
    """
    Allows adding a group to the currently selected points using
    a dropdown menu and add button. The current annotations are
    reflected in a table.

    Works by using a shared datasource on the Points and Table.
    """

    add = param.Action(default=lambda self: self.add_group(), precedence=1,
                       doc="""Button triggering add action.""")

    group = param.ObjectSelector()

    column = param.String(default='Group', constant=True)

    table_height = param.Integer(default=150, doc="Height of the table",
                                 precedence=-1)

    table_width = param.Integer(default=300, doc="Width of the table",
                                 precedence=-1)

    def __init__(self, groups, **params):
        super(PointWidgetAnnotator, self).__init__(**params)
        group_param = self.params('group')
        group_param.objects = groups
        group_param.default = groups[0]
        self.point_sel_stream = Selection1D(source=self.points)
        self._group_data = {g: [] for g in groups}
        self.table_stream = Stream.define('TableUpdate')(transient=True)

    def add_group(self, **kwargs):
        new_index = self.point_sel_stream.index
        for idx in new_index:
            if idx not in self._group_data[self.group]:
                self._group_data[self.group].append(idx)
            for g, inds in self._group_data.items():
                if g != self.group:
                    self._group_data[g] = [idx for idx in inds if idx not in new_index]
        self.table_stream.trigger([self.table_stream])

    def group_table(self):
        plot = dict(width=self.table_width, height=self.table_height)
        data = [(group, str(inds)) for group, inds in self._group_data.items()]
        return Table(data, self.column, 'index').sort().opts(plot=plot)

    def annotated_points(self):
        element = self.point_stream.element
        groups = []
        for g, idx in self._group_data.items():
            df = element.iloc[idx].dframe()
            df[self.column] = g
            groups.append(df)
        data = pd.concat(groups).sort_values(self.column) if groups else []
        return element.clone(data, vdims=self.column).opts(plot={'color_index': self.column},
                                                           style={'cmap': 'Category20'})

    def map_view(self):
        options = dict(tools=['box_select'], clone=False)
        annotated = DynamicMap(self.annotated_points, streams=[self.table_stream])
        return self.tiles * self.polys * self.points.options(**options) * annotated

    def table_view(self):
        return DynamicMap(self.group_table, streams=[self.table_stream])

    def panel(self):
        return pn.Row(self.param, self.map_view(), self.table_view())



class PolyAnnotator(GeoAnnotator):
    """
    Allows drawing and annotating Polygons using a bokeh DataTable.
    """

    poly_columns = param.List(default=['Group'], doc="""
        Columns to annotate the Polygons with.""", precedence=-1)

    vertex_columns = param.List(default=[], doc="""
        Columns to annotate the Polygons with.""", precedence=-1)

    table_height = param.Integer(default=150, doc="Height of the table",
                                 precedence=-1)

    table_width = param.Integer(default=400, doc="Width of the table",
                                 precedence=-1)

    def __init__(self, *args, **params):
        super(PolyAnnotator, self).__init__(*args, **params)
        self._link_polys()

    @param.depends('polys', watch=True)
    @preprocess
    def _link_polys(self):
        style = dict(editable=True)
        plot = dict(width=self.table_width, height=self.table_height)

        # Add annotation columns to poly data
        for col in self.poly_columns:
            if col not in self.polys:
                self.polys = self.polys.add_dimension(col, 0, '', True)
        self.poly_stream.source = self.polys
        self.vertex_stream.source = self.polys

        if len(self.polys):
            poly_data = gv.project(self.polys).split()
            self.poly_stream.event(data={kd.name: [p.dimension_values(kd) for p in poly_data]
                                         for kd in self.polys.kdims})

        poly_data = {c: self.polys.dimension_values(c, expanded=False) for c in self.poly_columns}
        if len(set(len(v) for v in poly_data.values())) != 1:
            raise ValueError('poly_columns must refer to value dimensions '
                             'which vary per path while at least one of '
                             '%s varies by vertex.' % self.poly_columns)
        self.poly_table = Table(poly_data, self.poly_columns, []).opts(plot=plot, style=style)
        self.poly_link = DataLink(source=self.polys, target=self.poly_table)
        self.vertex_table = Table([], self.polys.kdims, self.vertex_columns).opts(plot=plot, style=style)
        self.vertex_link = VertexTableLink(self.polys, self.vertex_table)

    @param.depends('points', 'polys')
    def map_view(self):
        return (self.tiles * self.polys.options(clone=False, line_width=5) *
                self.points.options(tools=['hover'], clone=False))

    @param.depends('polys')
    def table_view(self):
        return pn.Tabs(('Polygons', self.poly_table), ('Vertices', self.vertex_table))

    def panel(self):
        return pn.Row(self.map_view, self.table_view)

    @param.output(path=hv.Path)
    def path_output(self):
        return self.poly_stream.element



class PointAnnotator(GeoAnnotator):
    """
    Allows drawing and annotating Points using a bokeh DataTable.
    """

    point_columns = param.List(default=['Size'], doc="""
        Columns to annotate the Points with.""", precedence=-1)

    table_height = param.Integer(default=150, doc="Height of the table",
                                 precedence=-1)

    table_width = param.Integer(default=400, doc="Width of the table",
                                 precedence=-1)

    def __init__(self, *args, **params):
        super(PointAnnotator, self).__init__(*args, **params)
        self._link_points()

    @param.depends('points', watch=True)
    @preprocess
    def _link_points(self):
        style = dict(editable=True)
        plot = dict(width=self.table_width, height=self.table_height)
        for col in self.point_columns:
            if col not in self.points:
                self.points = self.points.add_dimension(col, 0, None, True)
        self.point_stream = PointDraw(source=self.points, data={})
        projected = gv.project(self.points, projection=ccrs.PlateCarree())
        self.point_table = Table(projected).opts(plot=plot, style=style)
        self.point_link = PointTableLink(source=self.points, target=self.point_table)

    @param.depends('points')
    def table_view(self):
        return self.point_table

    def panel(self):
        return pn.Row(self.map_view, self.table_view)

    @param.output(points=gv.Points)
    def point_output(self):
        return self.point_stream.element


class PolyAndPointAnnotator(PolyAnnotator, PointAnnotator):
    """
    Allows drawing and annotating Points and Polygons using a bokeh
    DataTable.
    """

    @param.depends('points', 'polys')
    def table_view(self):
        return pn.Tabs(('Polygons', self.poly_table), ('Vertices', self.vertex_table),
                       ('Points', self.point_table))


class PolyExporter(param.Parameterized):

    filename = param.String(default='')

    path = param.ClassSelector(class_=Path, precedence=-1)

    save = param.Action(default=lambda x: x._save())

    def __init__(self, path, **params):
        self._polys = paths_to_polys(path)
        super(PolyExporter, self).__init__(path=path, **params)

    def _save(self):
        pass

    def panel(self):
        return pn.Row(self.param, self._polys.options(width=800, height=600))


options = Store.options('bokeh')

options.Points = Options('plot', padding=0.1)
options.Points = Options('style', size=10, line_color='black')
options.Path = Options('plot', padding=0.1)
options.Polygons = Options('plot', padding=0.1)
