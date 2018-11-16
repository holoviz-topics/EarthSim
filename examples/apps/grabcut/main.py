import panel as pn
import geoviews as gv

from earthsim.annotators import PolyAnnotator, PolyExporter
from earthsim.grabcut import GrabCutPanel, SelectRegionPanel

gv.extension('bokeh')

stages = [
    ('Select Region', SelectRegionPanel),
    ('Grabcut', GrabCutPanel),
    ('Path Editor', PolyAnnotator),
    ('Polygon Exporter', PolyExporter)
]

pipeline = pn.pipeline.Pipeline(stages)

pipeline.layout.servable()
