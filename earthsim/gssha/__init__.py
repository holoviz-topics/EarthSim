"""
Support for running GSSHA simulations, using Quest.
"""

from datetime import datetime, timedelta

import param
import quest
import geopandas as gpd

from .model import CreateModel, CreateGSSHAModel


class Simulation(param.Parameterized):
    """Basic example of wrapping a GSSHA-based rainfall simulation."""
    
    elevation_service = param.Parameter(default='svc://usgs-ned:13-arc-second',precedence=0.1)
    
    land_use_service = param.Parameter(default='svc://usgs-nlcd:2011',precedence=0.2)

    land_use_grid_id = param.Parameter(default='nlcd',precedence=0.3)
    
    model_creator = param.ClassSelector(CreateModel,default=CreateGSSHAModel(),precedence=-1)

    # TODO: switch to date range...
    simulation_start=param.Date(default=datetime(2017, 5 ,9),precedence=0.5)
    # ...or at least a timedelta parameter type
    simulation_duration=param.Integer(default=120, bounds=(0,None), softbounds=(0,1000000), precedence=0.51, doc="""
        Simulated-time duration to run the simulator, in seconds.""")

    rain_intensity= param.Integer(default=24, bounds=(0,None), softbounds=(0,75), precedence=0.6, doc="""
        Intensity for simulated rain, in mm/hr.""")

    rain_duration=param.Integer(default=60,bounds=(0,None), softbounds=(0,1000000), precedence=0.61, doc="""
        Simulated-time duration for simulated rain, in seconds.""")


def download_data(service_uri, bounds, collection_name, use_existing=True):
    """
    Downloads raster data from source uri and adds to a quest collection.
    
    If multiple raster tiles are retrieved for the given bounds it calls a quest 
    filter to merge the tiles into a single raster.

    Returns the quest dataset name.
    """
    # download the features (i.e. locations) and metadata for the given web service
    # the first time this is run it will take longer since it downloads 
    # and caches all metadata for the given service.
    dataset_id = quest.api.get_seamless_data(
        service_uri=service_uri,
        bbox=bounds,
        collection_name=collection_name,
        as_open_dataset=False,
        raise_on_error=True,
    )

    return dataset_id


# TODO: need to understand how quest is being used by researchers. This temporary
# function eases development of the workflow by avoiding repeated downloads.
def get_file_from_quest(collection_name, service_uri, parameter, mask_shapefile, use_existing=True):
    """
    For a given collection_name, service_uri, parameter_name, and
    mask_shapefile, return quest's path to the corresponding file.

    If the given combination does not exist in quest, data will be 
    downloaded and then stored in quest.

    The parameter, mask_shapefile, and service are stored in the
    dataset's metadata.

    Note: service_uri=svc://dummy with
    collection_name=test_philippines_small skips quest completely
    and returns hardcoded 'philippines_small' data.
    """
    if service_uri == 'svc://dummy' and collection_name == 'test_philippines_small':
        if parameter == 'landuse':
            return 'philippines_small/LC_hd_global_2012.tif'
        elif parameter == 'elevation':
            return 'philippines_small/gmted_elevation.tif'
        else:
            raise ValueError
        
    bounds = [float(x) for x in gpd.read_file(mask_shapefile).geometry.bounds.values[0]]
    dataset_id = download_data(service_uri, bounds, collection_name, use_existing)
    metadata = quest.api.datasets.update_metadata(dataset_id, metadata={
        'mask_shapefile': mask_shapefile,
        'service_uri': service_uri,
        'parameter': parameter})[dataset_id]

    return metadata['file_path']
