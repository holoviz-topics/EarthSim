import * as p from "core/properties"
import {ActionTool, ActionToolView} from "models/tools/actions/action_tool"
import {ColumnDataSource} from "models/sources/column_data_source"


export class RestoreToolView extends ActionToolView {
  model: RestoreTool

  doit(): void {
    for (var source of this.model.sources) {
      if ((source.buffer == undefined) || (source.buffer.length == 0)) { continue; }
      source.data = source.buffer.pop();
      source.change.emit();
      source.properties.data.change.emit();
    }
  }
}

export namespace RestoreTool {
  export interface Attrs extends ActionTool.Attrs {}

  export interface Props extends ActionTool.Props {}
}

export interface RestoreTool extends RestoreTool.Attrs {}

export class RestoreTool extends ActionTool {
  properties: RestoreTool.Props
  sources: ColumnDataSource[]

  constructor(attrs?: Partial<RestoreTool.Attrs>) {
    super(attrs)
  }

  static initClass(): void {
    this.prototype.type = "RestoreTool"
    this.prototype.default_view = RestoreToolView

    this.define({
      sources: [ p.Array, [] ],
    })
  }

  tool_name = "Restore"
  icon = "bk-tool-icon-undo"
}

RestoreTool.initClass()
