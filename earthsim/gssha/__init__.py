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
    
    model_creator = param.ClassSelector(CreateModel,default=CreateGSSHAModel(),precedence=0.4)

    # TODO: switch to date range...
    simulation_start=param.Date(default=datetime(2017, 5 ,9),precedence=0.5)
    # ...or at least a timedelta parameter type
    simulation_duration=param.Integer(default=120, bounds=(0,None), softbounds=(0,1000000), precedence=0.51, doc="""
        Simulated-time duration to run the simulator, in seconds.""")

    rain_intensity= param.Integer(default=24, bounds=(0,None), softbounds=(0,75), precedence=0.6, doc="""
        Intensity for simulated rain, in mm/hr.""")

    rain_duration=param.Integer(default=60,bounds=(0,None), softbounds=(0,1000000), precedence=0.61, doc="""
        Simulated-time duration for simulated rain, in seconds.""")


    

def download_data(service_uri, bounds, collection_name):
    """
    Downloads raster data from source uri and adds to a quest collection.
    
    If multiple raster tiles are retrieved for the given bounds it calls a quest 
    filter to merge the tiles into a single raster.

    Returns the quest dataset name.
    """
    # download the features (i.e. locations) and metadata for the given web service
    # the first time this is run it will take longer since it downloads 
    # and caches all metadata for the given service.
    features = quest.api.get_features(uris=service_uri,
                                      filters={'bbox': bounds},
                                      as_dataframe=True,
                                      update_cache=False
                                      )
    
    # add the selected features to a quest collection
    added_features = quest.api.add_features(collection_name, features)
    
    # stage the data for download, optional parameters can be provided here 
    # for certain web services (i.e. date range etc), raster services don't 
    # typically have any optional parameters.
    staged_datasets = quest.api.stage_for_download(uris=added_features)
    
    # download the staged datasets
    quest.api.download_datasets(datasets=staged_datasets)
    final_datasets = staged_datasets
    
    # if more than one raster tile downloaded, merge into a single raster tile
    if len(staged_datasets) > 1:
        merged_datasets = quest.api.apply_filter(name='raster-merge',
                                                 datasets=staged_datasets)
        final_datasets = merged_datasets['datasets']
        # delete the original individual tiles
        quest.api.delete(staged_datasets)

    assert len(final_datasets)==1
    return final_datasets[0]


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

    if use_existing:
        for k,v in quest.api.get_datasets(expand=True).items():
            if v.get('collection','')==collection_name and \
               (v.get('metadata',{}) or {}).get('mask_shapefile') == mask_shapefile and \
               (v.get('metadata',{}) or {}).get('service_uri') == service_uri and \
               (v.get('metadata',{}) or {}).get('parameter') == parameter:
                return quest.api.open_dataset(k).name
        
    bounds = [str(x) for x in gpd.read_file(mask_shapefile).geometry.bounds.values[0]]
    d = download_data(service_uri,bounds,collection_name)
    quest.api.datasets.update_metadata(d,metadata={'mask_shapefile': mask_shapefile,
                                                   'service_uri': service_uri,
                                                   'parameter': parameter})
    return quest.api.open_dataset(d).name
