"""
Modeling gsshapy...

"""

import os

import geopandas as gpd
import param

from gsshapy.modeling import GSSHAModel


class RoughnessSpecification(param.Parameterized):
    __abstract = True
    
    # If we could modify code in gsshpy we could actually do something useful here 
    # (e.g. replacing code in GSSHAModel.set_roughness()), but probably for this initial
    # wrapping we should just return the right combo of arguments for GSSHAModel.
    def get_args(self):
        raise NotImplementedError

class UniformRoughness(RoughnessSpecification):
    
    # TODO: what default?
    value = param.Number(default=0.04, doc="""
       Value of uniform manning's n roughness for grid.""")
    
    def get_args(self):
        return {
            'roughness': self.value,
            'land_use_grid': None,
            'land_use_to_roughness_table': None,
            'land_use_grid_id': None
        }
    
# Need to rename/reorganize these - but can't quite make sense of the existing names 
# and docstrings. Would need to study code...

class GriddedRoughness(RoughnessSpecification):

    __abstract = True
    
    land_use_grid = param.FileSelector(default=None, doc="""
       Path to land use grid to use for roughness.""")

    def get_args(self):
        raise NotImplementedError
    
    
class GriddedRoughnessTable(GriddedRoughness):

    land_use_to_roughness_table = param.FileSelector(default=None, doc="""
       Path to land use to roughness table.""") 
    
    def get_args(self):
        return {
            'roughness': None,
            'land_use_grid': self.land_use_grid,
            'land_use_to_roughness_table': self.land_use_to_roughness_table,
            'land_use_grid_id': None
        }

class GriddedRoughnessID(GriddedRoughness):
    
    land_use_grid_id = param.String(default='nlcd', doc="""
       ID of default grid supported in GSSHApy. """)

    def get_args(self):
        return {
            'roughness': None,
            'land_use_grid': self.land_use_grid,
            'land_use_to_roughness_table': None,
            'land_use_grid_id': self.land_use_grid_id
        }   
    
    
# Hmm, the "required for new model" bit that was in every docstring makes me think there might
# be another option to consider too, but I haven't got that far yet...


class CreateModel(param.Parameterized):

    __abstract = True
    
    project_base_directory = param.Foldername(default=os.getcwd(), doc="""
       Base directory to which name will be appended to write GSSHA project files to.""", precedence=0)
    
    project_name = param.String(default='vicksburg_south', doc="Name of GSSHA project. Required for new model.")    

    def _map_kw(self,p):
        kw = {}
        kw['project_directory'] = os.path.abspath(os.path.join(p.project_base_directory, p.project_name))
        os.makedirs(kw['project_directory']) # TODO: decide what to do about overwriting
        kw['project_name'] = p.project_name
        return kw
    
    def __call__(self,**params):
        raise NotImplementedError


# TODO: precedence
# TODO: check about abs path requirement
# TODO: defaults are strange e.g. ./vicksburg_watershed/*.shp
    
    
class CreateGSSHModel(CreateModel):
    
    mask_shapefile = param.FileSelector(default='./vicksburg_watershed/watershed_boundary.shp',
                                        path='./vicksburg_watershed/*.shp', doc="""
       Path to watershed boundary shapefile. Required for new model. Typically a *.shp file.""", precedence=0.1)
    
    grid_cell_size = param.Number(default=None, precedence=0.2)

    # TODO: specify acceptable file extensions?
    elevation_grid_path = param.FileSelector(
        doc="""
       Path to elevation raster used for GSSHA grid. Required for new model. Typically an *.ele file.""", precedence=0.3)

    # TODO: paramnb ClassSelector should cache instances that get
    # created or else editing parameters on non-default options is
    # confusing.
    roughness = param.ClassSelector(RoughnessSpecification,default=UniformRoughness(),doc="""
        Specify roughness something something""") 

    out_hydrograph_write_frequency = param.Number(default=10, bounds=(1,60), doc="""
       Frequency of writing to hydrograph (minutes). Sets HYD_FREQ card. Required for new model.""", precedence=0.8)

        
    def _map_kw(self,p):
        kw = super(CreateGSSHModel,self)._map_kw(p)
        kw['mask_shapefile'] = p.mask_shapefile
        kw['grid_cell_size'] = p.grid_cell_size
        kw['elevation_grid_path'] = os.path.abspath(p.elevation_grid_path)
        kw['out_hydrograph_write_frequency'] = p.out_hydrograph_write_frequency
        kw.update(p.roughness.get_args())        
        return kw
        
        
    def __call__(self,**params):
        p = param.ParamOverrides(self,params)
        return GSSHAModel(**self._map_kw(p))


#class create_framework(param.ParameterizedFunction):
#    pass
