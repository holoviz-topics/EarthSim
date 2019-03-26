import * as p from "core/properties"
import {ActionTool, ActionToolView} from "models/tools/actions/action_tool"
import {ColumnDataSource} from "models/sources/column_data_source"


export class ClearToolView extends ActionToolView {
  model: ClearTool

  doit(): void {
    for (var source of this.model.sources) {
      for (const column in source.data) {
        source.data[column] = []
      }
      source.change.emit();
      source.properties.data.change.emit();
    }
  }
}

export namespace ClearTool {
  export type Attrs = p.AttrsOf<Props>
  export type Props = ActionTool.Props & {
    sources: p.Property<ColumnDataSource[]>
  }
}

export interface ClearTool extends ClearTool.Attrs {}

export class ClearTool extends ActionTool {
  properties: ClearTool.Props

  constructor(attrs?: Partial<ClearTool.Attrs>) {
    super(attrs)
  }

  static initClass(): void {
    this.prototype.type = "ClearTool"
    this.prototype.default_view = ClearToolView

    this.define<ClearTool.Props>({
      sources: [ p.Array, [] ],
    })
  }

  tool_name = "Clear data"
  icon = "bk-tool-icon-reset"
}

ClearTool.initClass()
