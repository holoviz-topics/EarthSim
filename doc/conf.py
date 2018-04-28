# -*- coding: utf-8 -*-

from nbsite.shared_conf import *

###################################################
# edit things below as appropriate for your project

project = u'EarthSim'
authors = u'GitHub contributors'
copyright = u'2018 ' + authors
description = 'Tools for working with and visualizing environmental simulations.'

version = '0.0.1'
release = '0.0.1'

html_static_path += ['_static']
html_theme = 'sphinx_ioam_theme'
# logo file etc should be in html_static_path, e.g. _static
html_theme_options = {
#    'custom_css':'bettercolors.css',
#    'logo':'amazinglogo.png',
#    'favicon':'amazingfavicon.ico'
}

nbbuild_cell_timeout = 1800

_NAV =  (
    ('Getting Started', 'getting_started/index'),
    ('User Guide', 'user_guide/index'),
    ('Topics', 'topics/index'),
    ('About', 'about')
)

html_context.update({
    'PROJECT': project,
    'DESCRIPTION': description,
    'AUTHOR': authors,
    # will work without this - for canonical (so can ignore when building locally or test deploying)    
    'WEBSITE_SERVER': 'https://pyviz.github.io/earthsim',
    'VERSION': version,
    'NAV': _NAV,
    # by default, footer links are same as those in header
    'LINKS': _NAV,
    'SOCIAL': (
        ('Github', '//github.com/pyviz/earthsim'),
    )
})

html_theme_options = {
    'logo':'logo.png',
    'favicon':'favicon.ico',
    'custom_css':'geoviews.css'
}
