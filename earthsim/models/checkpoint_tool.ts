import * as p from "core/properties"
import {copy} from "core/util/array"
import {ActionTool, ActionToolView} from "models/tools/actions/action_tool"
import {ColumnDataSource} from "models/sources/column_data_source"


export class CheckpointToolView extends ActionToolView {
  model: CheckpointTool

  doit(): void {
    for (var source of this.model.sources) {
      if (source.buffer == undefined) { source.buffer = [] }
      let data_copy = {};
      for (const key in source.data) {
        const column = source.data[key];
        const new_column = []
        for (const arr of column) {
          if (Array.isArray(arr) || (ArrayBuffer.isView(arr))) {
            new_column.push(copy(arr))
          } else {
            new_column.push(arr)
          }
        }
        data_copy[key] = new_column;
      }
      source.buffer.push(data_copy)
    }
  }
}

export namespace CheckpointTool {
  export interface Attrs extends ActionTool.Attrs {}

  export interface Props extends ActionTool.Props {}
}

export interface CheckpointTool extends CheckpointTool.Attrs {}

export class CheckpointTool extends ActionTool {
  properties: CheckpointTool.Props
  sources: ColumnDataSource[]

  constructor(attrs?: Partial<CheckpointTool.Attrs>) {
    super(attrs)
  }

  static initClass(): void {
    this.prototype.type = "CheckpointTool"
    this.prototype.default_view = CheckpointToolView

    this.define({
      sources: [ p.Array, [] ],
    })
  }

  tool_name = "Checkpoint"
  icon = "bk-tool-icon-save"
}
CheckpointTool.initClass()
