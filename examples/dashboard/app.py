import os

from bokeh.application.handlers import FunctionHandler
from bokeh.application import Application
import bokeh.layouts

from jinja2 import Environment, FileSystemLoader
from bokeh.themes.theme import Theme
from bokeh.models import Div

import param
import holoviews as hv

renderer = hv.renderer('bokeh')
renderer.mode='server'


class SharedState(object):
    """
    State to be shared between dashboards and dashboard elements.
    """

    def __init__(self):
        self._last_state = {}
        self.state = {}

    def set_state(self, **kwargs):
        for k,v in kwargs.items():
            if k in self.state:
                self._last_state[k] = self.state[k]
        for k,v in kwargs.items():
            self.state[k] = v

    def modified_state(self):
        modified = {}
        for k,v in self.state.items():
            last_val = self._last_state.get(k,None)
            if v != last_val:
                modified[k] = v
        return modified


shared_state = SharedState()



class App(object):
    """
    Mixin class to handle boilerplate necessary to turn holoviews
    objects into Bokeh applications.
    """

    name = 'Dashboard' # Title of the dashboard page

    def load_theme(self, **params):
        appindex = os.path.join('.', 'templates', 'index.html')
        env = Environment(loader=FileSystemLoader(os.path.dirname(appindex)))
        self.template = env.get_template('index.html')
        self.theme = Theme(filename='./templates/theme.yaml')


    def apply_theming(self, doc):
        doc._template = self.template
        doc.theme = self.theme


    def viewable(self):
        """
        Returns either a HoloViews viewable object (e.g. a DynamicMap
        with streams) or a Bokeh model.
        """
        raise NotImplementedError('Override viewable method in subclass')

    def doc_handler(self, doc):
        """
        Callback passed to the Bokeh FunctionHandler.
        """
        viewable = self.viewable(doc)
        if isinstance(viewable, hv.Dimensioned):
            doc = renderer.server_doc(viewable, doc=doc)
        else:
            doc.add_root(viewable)

        doc.title = self.name
        return doc

    def __call__(self):
        """
        Call to return a Bokeh Application to serve.
        """
        return Application(FunctionHandler(self.doc_handler))


class DashboardLayout(param.Parameterized):

    @classmethod
    def model(cls, hvobj, doc):
        """
        Given a HoloViews object return the corresponding Bokeh model.
        """
        return renderer.get_plot(hvobj, doc=doc).state

class DivLayout(DashboardLayout):

    def __init__(self, text, width, **params):
        self.text = text
        self.width = width
        super(DivLayout, self).__init__(**params)

    def __call__(self, shared_state, doc):
        return Div(text=self.text, width=self.width)


class ComposeLayouts(DashboardLayout):

    def __init__(self, layouts):
        self.layouts = layouts

    def __call__(self, shared_state, doc):

        models = []
        for row in self.layouts:
            models.append([None if l is None else l(shared_state, doc) for l in row])

        return bokeh.layouts.layout(models, sizing_mode='fixed')

    def periodic(self, shared_state, request_args):
        for row in self.layouts:
            for el in row:
                el.periodic(shared_state, request_args)


class ColumnLayouts(DashboardLayout):

    def __init__(self, layouts):
        self.layouts = layouts

    def __call__(self, shared_state, doc):
        return bokeh.layouts.column([l(shared_state, doc) for l in self.layouts], sizing_mode='fixed')


    def periodic(self, shared_state, request_args):
        for el in self.layouts:
            el.periodic(shared_state, request_args)



class RowLayouts(DashboardLayout):

    def __init__(self, layouts):
        self.layouts = layouts

    def __call__(self, shared_state, doc):
        return bokeh.layouts.row([l(shared_state, doc) for l in self.layouts], sizing_mode='fixed')


    def periodic(self, shared_state, request_args):
        for el in self.layouts:
            el.periodic(shared_state, request_args)
