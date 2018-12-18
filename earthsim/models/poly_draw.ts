import * as p from "core/properties"
import {UIEvent} from "core/ui_events"
import {keys} from "core/util/object"
import {isArray} from "core/util/types"
import {PolyDrawTool, PolyDrawToolView} from "models/tools/edit/poly_draw_tool"


export class PolyVertexDrawToolView extends PolyDrawToolView {
  model: PolyVertexDrawTool

  _split_path(x: number, y: number): void {
    for (let r=0; r<this.model.renderers.length; r++) {
      const renderer = this.model.renderers[r]
      const glyph: any = renderer.glyph
      const cds: any = renderer.data_source
      const [xkey, ykey] = [glyph.xs.field, glyph.ys.field]
      const xpaths = cds.data[xkey]
      const ypaths = cds.data[ykey]
      for (let index = 0; index < xpaths.length; index++) {
        const xs = xpaths[index]
        const ys = ypaths[index]
        for (let i = 0; i < xs.length; i++) {
          if ((xs[i] == x) && (ys[i] == y) && (i != 0) && (i != (xs.length-1))) {
            xpaths.splice(index+1, 0, xs.slice(i))
            ypaths.splice(index+1, 0, ys.slice(i))
            xs.splice(i+1)
            ys.splice(i+1)
            return
          }
        }
      }
    }
  }

  _snap_to_vertex(ev: UIEvent, x: number, y: number): [number, number] {
    if (this.model.vertex_renderer) {
      // If an existing vertex is hit snap to it
      const vertex_selected = this._select_event(ev, false, [this.model.vertex_renderer])
      const point_ds = this.model.vertex_renderer.data_source
      // Type once dataspecs are typed
      const point_glyph: any = this.model.vertex_renderer.glyph
      const [pxkey, pykey] = [point_glyph.x.field, point_glyph.y.field]
      if (vertex_selected.length) {
        const index = point_ds.selected.indices[0]
        if (pxkey)
          x = point_ds.data[pxkey][index]
        if (pykey)
          y = point_ds.data[pykey][index]
        this._split_path(x, y)
        point_ds.selection_manager.clear()
      }
    }
    return [x, y]
  }

  _set_vertices(xs: number[] | number, ys: number[] | number, styles): void {
    const point_glyph: any = this.model.vertex_renderer.glyph
    const point_cds = this.model.vertex_renderer.data_source
    const [pxkey, pykey] = [point_glyph.x.field, point_glyph.y.field]
    if (pxkey) {
      if (isArray(xs))
        point_cds.data[pxkey] = xs
      else
        point_glyph.x = {value: xs}
    }
    if (pykey) {
      if (isArray(ys))
        point_cds.data[pykey] = ys
      else
        point_glyph.y = {value: ys}
    }

    if (styles != null) {
      for (const key of keys(styles)) {
        point_cds.data[key] = styles[key] 
        point_glyph[key] = {field: key}
      }
    } else {
      for (const col of point_cds.columns()) {
        point_cds.data[col] = []
      }
    }
    this._emit_cds_changes(point_cds, true, true, false)
  }

  _show_vertices(): void {
    if (!this.model.active ) { return }
    const xs: number[] = []
    const ys: number[] = []
    const styles = {}
    for (const key of keys(this.model.end_style))
      styles[key] = []
    for (let i=0; i<this.model.renderers.length; i++) {
      const renderer = this.model.renderers[i]
      const cds = renderer.data_source
      const glyph: any = renderer.glyph
      const [xkey, ykey] = [glyph.xs.field, glyph.ys.field]
      for (const array of cds.get_array(xkey)) {
        Array.prototype.push.apply(xs, array)
        for (const key of keys(this.model.end_style))
          styles[key].push(this.model.end_style[key])
        for (const key of keys(this.model.node_style)) {
          for (let index = 0; index < (array.length-2); index++) { 
            styles[key].push(this.model.node_style[key])
          }
        }
        for (const key of keys(this.model.end_style))
          styles[key].push(this.model.end_style[key])
      }
      for (const array of cds.get_array(ykey))
        Array.prototype.push.apply(ys, array)
      if (this._drawing && (i == (this.model.renderers.length-1))) {
        // Skip currently drawn vertex
        xs.splice(xs.length-1, 1)
        ys.splice(ys.length-1, 1)
        for (const key of keys(styles))
          styles[key].splice(styles[key].length-1, 1)
      }
    }
    this._set_vertices(xs, ys, styles)
  }
}

export namespace PolyVertexDrawTool {
  export interface Attrs extends ActionTool.Attrs {}

  export interface Props extends ActionTool.Props {}
}

export interface PolyVertexDrawTool extends PolyDrawTool.Attrs {}

export class PolyVertexDrawTool extends PolyDrawTool {
  properties: PolyVertexDrawTool.Props
  sources: ColumnDataSource[]

  constructor(attrs?: Partial<PolyVertexDrawTool.Attrs>) {
    super(attrs)
  }

  static initClass(): void {
    this.prototype.type = "PolyVertexDrawTool"
    this.prototype.default_view = PolyVertexDrawToolView

    this.define({
      node_style: [ p.Any, {} ],
      end_style: [ p.Any, {} ],
    })
  }
}
PolyVertexDrawTool.initClass()
