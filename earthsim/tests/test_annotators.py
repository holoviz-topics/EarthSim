import numpy as np
import pandas as pd
import holoviews.plotting.bokeh
import geoviews.plotting.bokeh
import cartopy.crs as ccrs

from bokeh.models import ColumnDataSource, Plot, DataTable
from geoviews import Points, Polygons
from pyviz_comms import Comm

from earthsim.annotators import PointAnnotator, PolyAnnotator
from earthsim.links import PointTableLinkCallback, VertexTableLinkCallback

sample_poly = dict(
    Longitude = [-10114986, -10123906, -10130333, -10121522, -10129889, -10122959],
    Latitude  = [  3806790,   3812413,   3807530,   3805407,   3798394,   3796693]
)

sample_points = {
    'Longitude': [-10131185., -10131943., -10131766., -10131032.],
    'Latitude':  [  3805587.,   3803182.,   3801073.,   3799778.],
    'Size':      [        5,        50,       500,      5000]
}

def test_poly_annotator_init_models():
    annot = PolyAnnotator(poly_columns=['Group'], polys=[sample_poly], vertex_columns=['Weight'])
    panel = annot.panel()
    root_model = panel.get_root()

    fig = root_model.select_one({'type': Plot})
    polys = fig.renderers[1]
    table1, table2 = root_model.select({'type': DataTable})
    if 'xs' in table1.source.data:
        table1, table2 = table2, table1 # Ensure tables are correctly ordered

    # Ensure poly data matchs
    np.testing.assert_allclose(polys.data_source.data['xs'][0][:-1], sample_poly['Longitude'])
    np.testing.assert_allclose(polys.data_source.data['ys'][0][:-1], sample_poly['Latitude'])

    # Ensure table and poly data are lnked
    assert table2.source is polys.data_source

    # Ensure poly is linked to vertex table
    poly_cbs = polys.data_source.js_property_callbacks['change:data']
    assert len(poly_cbs) == 1
    assert poly_cbs[0].code == VertexTableLinkCallback.source_code

    table_cbs = table1.source.js_property_callbacks['change:data']
    assert len(table_cbs) == 1
    assert table_cbs[0].code == VertexTableLinkCallback.target_code


def test_poly_annotator_update_models():
    annot = PolyAnnotator(poly_columns=['Group'], polys=[sample_poly], vertex_columns=['Weight'])
    panel = annot.panel()
    root_model = panel.get_root(comm=Comm()) # Pass comm to ensure update is applied

    poly = Polygons([dict(sample_poly, Test=1)], vdims=['Test'], crs=ccrs.GOOGLE_MERCATOR)
    annot.poly_columns = ['Test']
    annot.polys = poly

    fig = root_model.select_one({'type': Plot})
    polys = fig.renderers[1]
    table1, table2 = root_model.select({'type': DataTable})
    if 'xs' in table1.source.data:
        table1, table2 = table2, table1 # Ensure tables are correctly ordered

    # Ensure poly data matches
    np.testing.assert_allclose(polys.data_source.data['xs'][0][:-1], sample_poly['Longitude'])
    np.testing.assert_allclose(polys.data_source.data['ys'][0][:-1], sample_poly['Latitude'])
    np.testing.assert_allclose(polys.data_source.data['Test'][0], np.ones(6))

    # Ensure table and poly data are linked
    assert table2.source is polys.data_source

    # Ensure poly is linked to vertex table
    poly_cbs = polys.data_source.js_property_callbacks['change:data']
    assert sum([cb.code == VertexTableLinkCallback.source_code
                for cb in poly_cbs]) == 1

    table_cbs = table1.source.js_property_callbacks['change:data']
    assert len(table_cbs) == 1
    assert table_cbs[0].code == VertexTableLinkCallback.target_code


def test_point_annotator_init_models():
    annot = PointAnnotator(point_columns=['Size'], points=sample_points)
    panel = annot.panel()
    root_model = panel.get_root()

    fig = root_model.select_one({'type': Plot})
    points = fig.renderers[-1]
    table = root_model.select_one({'type': DataTable})

    # Ensure points data matches
    for k in sample_points:
        np.testing.assert_allclose(points.data_source.data[k], sample_points[k])

    # Ensure point is linked to table
    point_cbs = points.data_source.js_property_callbacks['change:data']
    assert len(point_cbs) == 1
    assert point_cbs[0].code == PointTableLinkCallback.source_code

    table_cbs = table.source.js_property_callbacks['change:data']
    assert len(table_cbs) == 1
    assert table_cbs[0].code == PointTableLinkCallback.target_code


def test_point_annotator_updates():
    annot = PointAnnotator(point_columns=['Size'], points=sample_points)
    panel = annot.panel()
    root_model = panel.get_root(comm=Comm()) # Pass comm to ensure update is applied

    updated_points = dict(sample_points, Size=sample_points['Size'][::-1])
    points = Points(updated_points, vdims=['Size'], crs=ccrs.GOOGLE_MERCATOR)
    annot.points = points

    fig = root_model.select_one({'type': Plot})
    points = fig.renderers[-1]
    table = root_model.select_one({'type': DataTable})

    # Ensure points data matches
    for k in updated_points:
        np.testing.assert_allclose(points.data_source.data[k], updated_points[k])

    # Ensure point is linked to table
    point_cbs = points.data_source.js_property_callbacks['change:data']
    assert len(point_cbs) == 1
    assert point_cbs[0].code == PointTableLinkCallback.source_code

    table_cbs = table.source.js_property_callbacks['change:data']
    assert len(table_cbs) == 1
    assert table_cbs[0].code == PointTableLinkCallback.target_code
