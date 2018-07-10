import param

from holoviews.element import Path, Table
from holoviews.plotting.links import Link
from holoviews.plotting.bokeh.callbacks import LinkCallback
from holoviews.core.util import dimension_sanitizer

class VertexTableLink(Link):
    """
    Defines a Link between a Path type and a Table which will
    display the vertices of selected path.
    """

    source = param.ClassSelector(class_=Path)

    target = param.ClassSelector(class_=Table)

    vertex_columns = param.List(default=[])

    def __init__(self, source, target, **params):
        if 'vertex_columns' not in params:
            dimensions = [dimension_sanitizer(d.name) for d in target.dimensions()[:2]]
            params['vertex_columns'] = dimensions
        super(VertexTableLink, self).__init__(source, target, **params)


class VertexTableLinkCallback(LinkCallback):

    source_model = 'cds'
    source_handles = ['glyph_renderer']
    target_model = 'cds'
    target_handles = ['glyph_renderer']

    on_source_changes = ['selected', 'data']
    on_target_changes = ['data']

    source_code = """
    var projections = require("core/util/projections");
    if (!source_cds.selected.indices.length) { return }
    index = source_cds.selected.indices[0]
    xs_column = source_cds.data['xs'][index]
    ys_column = source_cds.data['ys'][index]
    var projected_xs = []
    var projected_ys = []
    var empty = []
    for (i = 0; i < xs_column.length; i++) {
      var x = xs_column[i]
      var y = ys_column[i]
      p = projections.wgs84_mercator.inverse([x, y])
      projected_xs.push(p[0])
      projected_ys.push(p[1])
      empty.push(null)
    }
    [x, y] = vertex_columns
    target_cds.data[x] = projected_xs
    target_cds.data[y] = projected_ys
    var length = projected_xs.length
    for (var col in target_cds.data) {
      if (vertex_columns.indexOf(col) != -1) { continue; }
      else if (col in source_cds.data) {
        var path = source_cds.data[col][index];
        if ((path == undefined)) {
          data = empty;
        } else if (path.length == length) {
          data = source_cds.data[col][index];
        } else {
          data = empty;
        }
      } else {
        data = empty;
      }
      target_cds.data[col] = data;
    }
    target_cds.change.emit()
    """

    target_code = """
    var projections = require("core/util/projections");
    if (!source_cds.selected.indices.length) { return }
    [x, y] = vertex_columns
    xs_column = target_cds.data[x]
    ys_column = target_cds.data[y]
    var projected_xs = []
    var projected_ys = []
    for (i = 0; i < xs_column.length; i++) {
      var xv = xs_column[i]
      var yv = ys_column[i]
      p = projections.wgs84_mercator.forward([xv, yv])
      projected_xs.push(p[0])
      projected_ys.push(p[1])
    }
    index = source_cds.selected.indices[0]
    source_cds.data['xs'][index] = projected_xs;
    source_cds.data['ys'][index] = projected_ys;
    var length = source_cds.data['xs'].length
    for (var col in target_cds.data) {
      if ((col == x) || (col == y)) { continue; }
      if (!(col in source_cds.data)) {
        var empty = []
        for (i = 0; i < length; i++)
          empty.push([])
        source_cds.data[col] = empty
      }
      source_cds.data[col][index] = target_cds.data[col]
    }
    source_cds.change.emit()
    source_cds.properties.data.change.emit();
    """

VertexTableLink.register_callback('bokeh', VertexTableLinkCallback)
