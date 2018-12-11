import os

from bokeh.core.properties import Instance, List, Dict, String, Any
from bokeh.core.enums import Dimensions
from bokeh.models import Tool, ColumnDataSource, PolyEditTool

from . import _CUSTOM_MODELS

fpath = os.path.dirname(__file__)


class CheckpointTool(Tool):
    """
    Checkpoints the data on the supplied ColumnDataSources, allowing
    the RestoreTool to restore the data to a previous state.
    """

    sources = List(Instance(ColumnDataSource))

    __implementation__ = os.path.join(fpath, 'checkpoint_tool.ts')


class RestoreTool(Tool):
    """
    Restores the data on the supplied ColumnDataSources to a previous
    checkpoint created by the CheckpointTool
    """

    sources = List(Instance(ColumnDataSource))

    __implementation__ = os.path.join(fpath, 'restore_tool.ts')


class ClearTool(Tool):
    """
    Clears the data on the supplied ColumnDataSources.
    """

    sources = List(Instance(ColumnDataSource))

    __implementation__ = os.path.join(fpath, 'clear_tool.ts')


class PolyVertexEditTool(PolyEditTool):

    node_style = Dict(String, Any, help="""
    Custom styling to apply to the intermediate nodes of a patch or line glyph.""")

    end_style = Dict(String, Any, help="""
    Custom styling to apply to the start and nodes of a patch or line glyph.""")

    __implementation__ = os.path.join(fpath, 'poly_edit.ts')


_CUSTOM_MODELS['earthsim.models.custom_tools.CheckPointTool'] = CheckpointTool
_CUSTOM_MODELS['earthsim.models.custom_tools.RestoreTool'] = RestoreTool
_CUSTOM_MODELS['earthsim.models.custom_tools.ClearTool'] = ClearTool
_CUSTOM_MODELS['earthsim.models.custom_tools.PolyVertexEditTool'] = PolyVertexEditTool
