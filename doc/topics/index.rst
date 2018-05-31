******
Topics
******

The `User Guide <../user_guide/>`_ has examples focusing on the ``earthsim`` code,
whereas these notebooks show case studies and in-depth examples of specific workflows and
research topics.  So far, the examples mostly use the
`GSSHA <http://www.gsshawiki.com/>`_ simulator, but other examples using
`AdH <http://www.erdc.usace.army.mil/Media/Fact-Sheets/Fact-Sheet-Article-View/Article/476708/adaptive-hydraulics-model-system/>`_ are being developed and will be added here when they are ready.

EarthSim is an open-source project, but note that the GSSHA simulator used in these examples is freely available but closed source.  GSSHA is also currently limited to Python 3.5 on Linux or Mac; Windows is not yet supported (unlike for the other EarthSim tools and examples).

* `GrabCut Demo <GrabCut.html>`_
  An example for using the GrabCut algorithm with OpenCV to extract a coastline from a satellite image

* `GSSHA Workflow <GSSHA_Workflow.html>`_
  An end to end workflow for running GSSHA simulations.

* `GSSHA Parameter Sweep <GSSHA_Parameter_Sweep.html>`_
  Running a parameter sweep of a parameterized GSSHA Workflow.

.. toctree::
    :titlesonly:
    :hidden:
    :maxdepth: 2

    GrabCut Demo <GrabCut>
    GSSHA Workflow <GSSHA_Workflow>
    GSSHA Parameter Sweep <GSSHA_Parameter_Sweep>

