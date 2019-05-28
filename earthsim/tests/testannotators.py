import numpy as np
import pandas as pd
import holoviews.plotting.bokeh

from bokeh.models import ColumnDataSource, Plot, DataTable

from earthsim.annotators import PointAnnotator, PolyAnnotator
from earthsim.links import PointTableLinkCallback, VertexTableLinkCallback


sample_poly=dict(
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
    tiles, polys, p1, p2, p3 = fig.renderers
    table1, table2 = root_model.select({'type': DataTable})

    np.testing.assert_allclose(polys.data_source.data['xs'][0][:-1], sample_poly['Longitude'])
    np.testing.assert_allclose(polys.data_source.data['ys'][0][:-1], sample_poly['Latitude'])

    assert table2.source is polys.data_source
    
    poly_cbs = polys.data_source.js_property_callbacks['change:data']
    assert len(poly_cbs) == 1
    assert poly_cbs[0].code == VertexTableLinkCallback.source_code

    table_cbs = table1.source.js_property_callbacks['change:data']
    assert len(table_cbs) == 1
    assert table_cbs[0].code == VertexTableLinkCallback.target_code


def test_point_annotator_init_models():
    annot = PointAnnotator(point_columns=['Size'], points=sample_points)
    panel = annot.panel()
    root_model = panel.get_root()

    fig = root_model.select_one({'type': Plot})
    tiles, polys, p1, p2, p3 = fig.renderers
    table = root_model.select_one({'type': DataTable})

    for k in sample_points:
        np.testing.assert_allclose(p3.data_source.data[k], sample_points[k])

    point_cbs = p3.data_source.js_property_callbacks['change:data']
    assert len(point_cbs) == 1
    assert point_cbs[0].code == PointTableLinkCallback.source_code

    table_cbs = table.source.js_property_callbacks['change:data']
    assert len(table_cbs) == 1
    assert table_cbs[0].code == PointTableLinkCallback.target_code
