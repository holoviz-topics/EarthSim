from functools import partial

import param
import pandas as pd
import cartopy.crs as ccrs

import holoviews as hv
from holoviews import DynamicMap, Path, Table, NdOverlay
from holoviews.streams import Selection1D, Stream, PolyDraw, PolyEdit, PointDraw, CDSStream
from geoviews import Polygons, Points, WMTS, TriMesh


class GeoAnnotator(param.Parameterized):
    """
    Provides support for drawing polygons and points on top of a map.
    """

    tile_url = param.String(default='http://c.tile.openstreetmap.org/{Z}/{X}/{Y}.png',
                            doc="URL for the tile source", precedence=-1)

    extent = param.NumericTuple(default=(-91, 32.2, -90.8, 32.4), doc="""
         Initial extent if no data is provided.""", precedence=-1)

    height = param.Integer(default=500, doc="Height of the plot",
                           precedence=-1)

    width = param.Integer(default=900, doc="Width of the plot",
                          precedence=-1)

    def __init__(self, polys=None, points=None, **params):
        super(GeoAnnotator, self).__init__(**params)
        plot_opts = dict(height=self.height, width=self.width)
        self.tiles = WMTS(self.tile_url, extents=self.extent,
                          crs=ccrs.PlateCarree()).opts(plot=plot_opts)
        polys = [] if polys is None else polys
        points = [] if points is None else points
        self.polys = Polygons(polys, crs=ccrs.GOOGLE_MERCATOR)
        self.poly_stream = PolyDraw(source=self.polys, data={})
        self.vertex_stream = PolyEdit(source=self.polys)
        self.points = Points(points, crs=ccrs.GOOGLE_MERCATOR)
        self.point_stream = PointDraw(source=self.points, data={})

    def pprint(self):
        params = dict(self.get_param_values())
        name = params.pop('name')
        string = '%s\n%s\n\n' % (name, '-'*len(name))
        for item in sorted(params.items()):
            string += '  %s: %s\n' % (item)
        print(string)

    def view(self):
        return self.tiles * self.polys * self.points



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
        plot = dict(width=self.width, height=self.table_height)
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

    def view(self):
        table = DynamicMap(self.group_table, streams=[self.table_stream])
        annotated = DynamicMap(self.annotated_points, streams=[self.table_stream])
        return (self.tiles * self.polys * self.points * annotated + table).cols(1)



class PolyAnnotator(GeoAnnotator):
    """
    Allows drawing and annotating Polygons using a bokeh DataTable.
    """

    poly_columns = param.List(default=['Group'], doc="""
        Columns to annotate the Polygons with.""", precedence=-1)

    table_height = param.Integer(default=150, doc="Height of the table",
                                 precedence=-1)

    def __init__(self, **params):
        super(PolyAnnotator, self).__init__(**params)
        self.poly_table_stream = CDSStream(data={}, rename={'data': 'table_data'})
        self.poly_sel_stream = Selection1D(source=self.polys)
        streams = [self.poly_stream, self.poly_sel_stream, self.poly_table_stream]
        self.poly_table = DynamicMap(self.load_table, streams=streams)
        sel_stream = Selection1D(source=self.poly_table)
        self.poly_view = DynamicMap(self.highlight_polys, streams=[sel_stream])


    def load_table(self, data, index, table_data):
        """
        Returns a table combining the data from two sources. The
        point or polygon data being annotated and the data from the
        table itself, which is used to annotate the points and
        polygons. Additionally receives the indices of selected points
        or polygons which are used to determine points to be deleted.
        """
        length = len(list(data.values())[0]) if data else 0
        if length:
            col_data = {}
            for col in self.poly_columns:
                vals = table_data.get(col, [])
                new = length-len(vals)
                if new < 0:
                    # Process deleted entry
                    if not index:
                        # Deletion has already been processed,
                        # skip and return last Table
                        return self.table.last
                    vals = [vals[idx] for idx in range(length)
                            if idx not in index]
                else:
                    # Process added entry
                    vals = vals + ['' for i in range(new)]
                col_data[col] = vals
            data = dict(index=range(length), **col_data)
        else:
            data = []
        style = dict(editable=True)
        plot = dict(width=self.width, height=self.table_height)
        return Table(data, 'index', self.poly_columns).opts(style=style, plot=plot)

    def highlight_polys(self, index):
        polys = self.poly_stream.element.split(datatype='array')
        selected = [arr for i, arr in enumerate(polys) if i in index]
        return Polygons(selected, crs=ccrs.GOOGLE_MERCATOR).opts(style=dict(fill_alpha=1))

    def view(self):
        sel_stream = Selection1D(source=self.poly_table)
        poly_view = DynamicMap(self.highlight_polys, streams=[sel_stream])
        return (self.tiles * self.polys * poly_view *
                self.points + self.poly_table).cols(1)


class PointAnnotator(GeoAnnotator):
    """
    Allows drawing and annotating Points using a bokeh DataTable.
    """

    point_columns = param.List(default=['Size'], doc="""
        Columns to annotate the Points with.""", precedence=-1)

    table_height = param.Integer(default=150, doc="Height of the table",
                                 precedence=-1)

    def __init__(self, **params):
        super(PointAnnotator, self).__init__(**params)
        style = dict(editable=True)
        plot = dict(width=self.width, height=self.table_height)
        for col in self.point_columns:
            self.points = self.points.add_dimension(col, 0, None, True)
        self.point_stream = PointDraw(source=self.points, data={})
        self.point_table = Table(self.points).opts(plot=plot, style=style)

    def view(self):
        layout = (self.tiles * self.polys * self.points + self.point_table)
        return hv.opts({'Layout': {'plot': dict(shared_datasource=True)}}, layout).cols(1)


class PolyAndPointAnnotator(PolyAnnotator, PointAnnotator):
    """
    Allows drawing and annotating Points and Polygons using a bokeh
    DataTable.
    """

    def view(self):
        return (self.tiles * self.polys * self.poly_view * self.points +
                self.poly_table + self.point_table).cols(1)
