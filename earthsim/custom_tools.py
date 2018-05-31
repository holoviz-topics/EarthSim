import os

from bokeh.core.properties import Instance, List
from bokeh.core.enums import Dimensions
from bokeh.models import Tool, ColumnDataSource

fpath = os.path.dirname(__file__)


class CheckpointTool(Tool):
    """
    Checkpoints the data on the supplied ColumnDataSources, allowing
    the RestoreTool to restore the data to a previous state.
    """

    __implementation__ = os.path.join(fpath, 'custom_tools.ts')
    
    sources = List(Instance(ColumnDataSource))


class RestoreTool(Tool):
    """
    Restores the data on the supplied ColumnDataSources to a previous
    checkpoint created by the CheckpointTool
    """

    __implementation__ = os.path.join(fpath, 'custom_tools.ts')
    
    sources = List(Instance(ColumnDataSource))
