import numpy as np
import panel as pn
import geoviews as gv
import cartopy.crs as ccrs
import xmsmesh
import pandas as pd
from geoviews import opts, tile_sources as gvts
import param

from earthsim.annotators import PolyAndPointAnnotator


def xmsmesh_to_dataframe(pts, cells):
    """
    Convert mesh pts and cells to dataframe

    Args:
      pts (MultiPolyMesherIo.points): Points from a MultiPolyMesherIo
      cells (MultiPolyMesherIo.cells: Cells from a MultiPolyMesherIo

    Returns:
      pd.DataFrame: MultiPolyMesherIo points in a dataframe
      pd.DataFrame: MultiPolyMesherIo cells in a dataframe
    """
    r_pts = pd.DataFrame(pts, columns=['x', 'y', 'z'])
    r_cells = pd.DataFrame([(cells[ x +2], cells[ x +3], cells[ x +4]) for x in range(0, len(cells), 5)], columns=['v0', 'v1', 'v2'])
    return r_pts, r_cells


class GenerateMesh(param.Parameterized):
    node_spacing = param.Number(default=1000, bounds=(0, None), softbounds=(10, 1000), label='Polygon Edge Spacing')

    vert_points = param.ClassSelector(default=gv.Points([]), class_=gv.Points, precedence=-1)
    cells = param.ClassSelector(default=pd.DataFrame(), class_=pd.DataFrame, precedence=-1)

    def __init__(self, polys=None, points=None, **params):
        super(GenerateMesh, self).__init__(**params)

        self.annot = PolyAndPointAnnotator(polys=polys, point_columns=['Size'], points=points)

    def create_mesh(self):
        # Add refine points
        points = self.annot.point_stream.element

        refine_points = []
        for x, y, s in zip(*(points.dimension_values(i) for i in range(3))):
            if s:
                refine_points.append(
                    xmsmesh.meshing.RefinePoint(create_mesh_point=True, point=(x, y, 0), size=float(s)))

            else:
                print('refine point {}, {} skipped due to missing size value'.format(x, y))

        input_polygon = []

        # add each polygon to the input data
        for ply in self.annot.poly_stream.element.split(datatype='dataframe'):
            # add an additional dimension as zeros (for required dimensionality)
            poly_data = np.hstack((ply[['Longitude', 'Latitude']].values, np.zeros((len(ply['Latitude']), 1))))
            # instantiate the redistribution class
            rdp = xmsmesh.meshing.PolyRedistributePts()
            # set the node distance
            rdp.set_constant_size_func(self.node_spacing)  # create_constant_size_function
            # run the redistribution function
            outdata = rdp.redistribute(poly_data)

            # convert the polygon to an 'input polygon'
            input_polygon.append(xmsmesh.meshing.PolyInput(outside_polygon=outdata))

        # add the input polygons as polygons to the mesher class
        self.mesh_io = xmsmesh.meshing.MultiPolyMesherIo(poly_inputs=input_polygon, refine_points=refine_points)

        # Generate Mesh
        succeded, errors = xmsmesh.meshing.mesh_utils.generate_mesh(mesh_io=self.mesh_io)

        # convert the xms data format into dataframes
        pts, self.cells = xmsmesh_to_dataframe(self.mesh_io.points, self.mesh_io.cells)

        # convert the pts df into a hv Points class
        self.vert_points = gv.Points(pts, vdims=['z'], crs=ccrs.GOOGLE_MERCATOR)

    @param.output(('vert_points', gv.Points), ('cells', pd.DataFrame))
    def output(self):
        self.create_mesh()
        return self.vert_points, self.cells

    def panel(self):
        map_view = self.annot.map_view().opts(height=600, width=600) * gvts.EsriImagery

        return pn.Row(pn.Column(map_view, pn.panel(self.param, parameters=['create'], show_name=False)),
                      pn.Column(self.annot.point_table,
                                pn.panel(self.param, parameters=['node_spacing'], show_name=False)))


class ViewMesh(param.Parameterized):
    vert_points = param.ClassSelector(default=gv.Points([]), class_=gv.Points, precedence=-1)
    cells = param.ClassSelector(default=pd.DataFrame(), class_=pd.DataFrame, precedence=-1)

    def __init__(self, vert_points, cells, **params):
        super(ViewMesh, self).__init__(vert_points=vert_points, cells=cells, **params)

    def view(self):
        # create the trimesh for displaying unstructured grids
        trimesh = gv.TriMesh((self.cells, self.vert_points))

        return trimesh.edgepaths.opts(line_width=0.5, height=600, width=600, line_color='yellow') * gvts.EsriImagery

    def panel(self):
        return pn.Column(self.view)

