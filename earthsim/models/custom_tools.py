import os

from bokeh.core.properties import Instance, List
from bokeh.core.enums import Dimensions
from bokeh.models import Tool, ColumnDataSource

from . import _CUSTOM_MODELS

fpath = os.path.dirname(__file__)


class CheckpointTool(Tool):
    """
    Checkpoints the data on the supplied ColumnDataSources, allowing
    the RestoreTool to restore the data to a previous state.
    """

    __implementation__ = os.path.join(fpath, 'checkpoint_tool.ts')

    sources = List(Instance(ColumnDataSource))


class RestoreTool(Tool):
    """
    Restores the data on the supplied ColumnDataSources to a previous
    checkpoint created by the CheckpointTool
    """

    __implementation__ = os.path.join(fpath, 'restore_tool.ts')

    sources = List(Instance(ColumnDataSource))


class ClearTool(Tool):
    """
    Clears the data on the supplied ColumnDataSources.
    """

    __implementation__ = os.path.join(fpath, 'clear_tool.ts')

    sources = List(Instance(ColumnDataSource))


_CUSTOM_MODELS['earthsim.models.custom_tools.CheckPointTool'] = CheckpointTool
_CUSTOM_MODELS['earthsim.models.custom_tools.RestoreTool'] = RestoreTool
_CUSTOM_MODELS['earthsim.models.custom_tools.ClearTool'] = ClearTool
