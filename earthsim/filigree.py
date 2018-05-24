"""
Interface to the Filigree irregular triangular mesh generator, 
allowing interactively specified control over mesh generation using Bokeh.
"""

from collections import defaultdict

import param
import cartopy.crs as ccrs
import filigree
from holoviews import Points, DynamicMap, Callable
from holoviews.streams import Stream, RangeXY
from geoviews import TriMesh, Points as GvPoints, RGB
from shapely.geometry import Polygon, Point
from holoviews.operation.datashader import datashade
from geoviews.operation import project_path, project_points

from .annotators import GeoAnnotator, PointAnnotator, PolyAnnotator


def viz_mesh(verts, tris):
    points = Points(verts, vdims=['z'])
    return TriMesh((tris, points), crs=ccrs.GOOGLE_MERCATOR)


def fix_poly(p):
    boundary = p.exterior
    holes = []
    if boundary.is_ccw:
        boundary.coords = list(boundary.coords)[::-1]
    for h in p.interiors:
        if not h.is_ccw:
            h.coords = list(h.coords)[::-1]
        holes.append(h.coords)
    return Polygon(boundary.coords, holes)


class FiligreeMesh(Stream):
    """
    Creates a FiligreeMesh given a DrawingHelper instance,
    which supplies the polygons and refine points.
    """

    crs = param.ClassSelector(class_=ccrs.Projection)
    
    draw_helper = param.ClassSelector(class_=GeoAnnotator)

    def __init__(self, draw_helper, **params):
        super(FiligreeMesh, self).__init__(draw_helper=draw_helper, **params)
        if not draw_helper.poly_stream.element:
            raise ValueError("Must draw polygon before running mesh.")
        self.mesh = filigree.FiligreeMesh()
        self.polys = self._process_polys(draw_helper.poly_stream.element)
        self.refine_points = self.add_refine_points(draw_helper)


    def _process_polys(self, element):
        if self.crs:
            element = project_path(element, projection=self.crs)
        polys = [Polygon(arr) for arr in element.split(datatype='array')]

        # Resolve polygons contained within other polygons as holes
        poly_ids = {}
        poly_holes = defaultdict(list)
        while polys:
            poly = polys.pop(0)
            found = False
            for subpoly in polys:
                if poly.contains(subpoly):
                    found = True
                    polys.pop(polys.index(subpoly))
                    poly_holes[id(poly)].append(subpoly)
                    poly_ids[id(poly)] = poly
                elif subpoly.contains(poly):
                    found = True
                    polys.pop(polys.index(subpoly))
                    poly_holes[id(subpoly)].append(poly)
                    poly_ids[id(subpoly)] = subpoly
            if not found:
                poly_ids[id(poly)] = poly
                poly_holes[id(poly)] = []

        # Create holes from polygons
        polys = []
        for poly_id, holes in poly_holes.items():
            poly = poly_ids[poly_id]
            holes = [hole.exterior for hole in holes]
            poly = fix_poly(Polygon(poly.exterior, holes=holes))
            self.mesh.add_polygon(poly)
            polys.append(poly)
        return polys


    def add_refine_points(self, helper):
        if not isinstance(helper, PointAnnotator):
            return []
        points = helper.points.clone(helper.point_stream.data)
        if self.crs:
            points = project_points(points, projection=crs)
        elif 'Size' not in helper.point_columns:
            return []

        refine_points = []
        for x, y, s in zip(*(points.dimension_values(i) for i in range(3))):
            if not any(p.contains(Point(x, y)) for p in self.polys):
                self.warning('refine point (%.3f, %.3f) not contained within polygon'
                             % (x, y))
                continue
            elif s:
                point = (x, y, float(s))
                self.mesh.add_refine_point(*point)
                refine_points.append(point)
        return refine_points


    def view(self):
        helper = self.draw_helper
        verts, tris = self.mesh.create_mesh()
        trimesh = viz_mesh(verts, tris)
        shaded_mesh = datashade(trimesh.edgepaths, cmap=['#000000'])
        return helper.tiles * shaded_mesh * helper.point_stream.element



class FiligreeMeshDashboard(FiligreeMesh):
    """
    An extension of FiligreeMesh which allows generating the mesh
    on the same plot as the polygons and refine points.
    """

    crs = param.ClassSelector(class_=ccrs.Projection, precedence=-1)

    draw_helper = param.ClassSelector(class_=GeoAnnotator, precedence=-1)

    clear_mesh = param.Action(default=lambda self: self._clear_mesh(), precedence=1,
                               doc="""Button clearing the current mesh.""")
    
    update_mesh = param.Action(default=lambda self: self.event(), precedence=1,
                               doc="""Button triggering mesh generation.""")

    def __init__(self, draw_helper, **params):
        super(FiligreeMesh, self).__init__(draw_helper=draw_helper, **params)
        self.mesh = filigree.FiligreeMesh()
        self._clear = False

    def _clear_mesh(self):
        self._clear = True
        self.event()

    def _reset_mesh(self):
        self.mesh.polygons = []
        self.mesh.refine_points = []

    def gen_mesh(self, **kwargs):
        if not self.draw_helper.poly_stream.element or self._clear:
            self._clear = False
            return RGB([], bounds=self.draw_helper.extent)
        self._reset_mesh()
        self.polys = self._process_polys(self.draw_helper.poly_stream.element)
        self.refine_points = self.add_refine_points(self.draw_helper)
        verts, tris = self.mesh.create_mesh()
        return datashade(viz_mesh(verts, tris).edgepaths, cmap=['#000000'],
                         dynamic=False)

    def view(self):
        helper = self.draw_helper
        mesh_dmap = DynamicMap(Callable(self.gen_mesh, memoize=False), streams=[self])
        if isinstance(helper, PolyAnnotator):
            layout = (helper.tiles * helper.polys * mesh_dmap * helper.points +
                      helper.poly_table + helper.point_table)
        else:
            layout = (helper.tiles * helper.polys * mesh_dmap * helper.points +
                      helper.point_table)
        return layout.options(shared_datasource=True, clone=False).cols(1)
