"""
Input and output for geo-specific data formats.
"""

import numpy as np
import pandas as pd
import fiona
import geoviews as gv
import dask.dataframe as dd
import xarray as xr
import cartopy.crs as ccrs

from osgeo import gdal, osr


def get_sampling(bounds, shape):
    """
    Generates x/y coordinates from bounds and shape.
    
    Parameters
    ----------
    
    bounds - tuple(float, float, float, float)
        north, south, east, west
    shape - tuple(int, int)
        rows, cols
    """
    rows, cols = shape
    y1, y0, x1, x0 = bounds
    xunit = (x1-x0)/cols/2.
    yunit = (y1-y0)/rows/2.
    xs = np.linspace(x0+xunit, x1-xunit, cols)
    ys = np.linspace(y0+yunit, y1-yunit, rows)
    return xs, ys


def open_gssha(filename):
    """
    Reads various filetypes produced by GSSHA
    """
    # Read metadata
    ftype = filename.split('.')[-1]
    if ftype in ['fgd', 'asc']:
        f = open(filename, 'r')
        c, r, xlc, ylc, gsize, nanval = [
            t(f.readline().split(' ')[-1].split('\n')[0])
            for t in [int, int, float, float, float, float]
        ]
        xs = np.linspace(xlc+gsize/2., xlc+c*gsize-gsize/2., c+1)
        ys = np.linspace(ylc+gsize/2., ylc+r*gsize-gsize/2., r)
    else:
        header_df = pd.read_table(filename, engine='python',
                              names=['meta_key', 'meta_val'],
                              sep=' ', nrows=6)
        bounds = header_df.loc[:3, 'meta_val'].values.astype(float)
        r, c = header_df.loc[4:6, 'meta_val'].values.astype(int)
        xs, ys = get_sampling(bounds, (r, c))
    
    # Read data using dask
    ddf = dd.read_csv(filename, skiprows=6, header=None,
                      sep=' ')
    darr = ddf.values.compute()
        
    if ftype == 'fgd':
        darr[darr==nanval] = np.NaN
    
    return xr.DataArray(darr[::-1], coords={'x': xs, 'y': ys},
                        name='z', dims=['y', 'x'])


def get_ccrs(filename):
    """
    Loads WKT projection string from file and return
    cartopy coordinate reference system.
    """
    inproj = osr.SpatialReference()
    proj = open(filename, 'r').readline()
    inproj.ImportFromWkt(proj)
    projcs = inproj.GetAuthorityCode('PROJCS')
    return ccrs.epsg(projcs)


def read_3dm_mesh(fpath, skiprows=1):
    """
    Reads a 3DM mesh file and returns the simplices and vertices as dataframes

    Parameters
    ----------

    fpath: str
         Path to 3dm file

    Returns
    -------

    tris: DataFrame
        Simplexes of the mesh
    verts: DataFrame
        Vertices of the mesh
    """
    all_df = pd.read_table(fpath, delim_whitespace=True, header=None, skiprows=skiprows,
                           names=('row_type', 'cmp1', 'cmp2', 'cmp3', 'val'), index_col=1)

    conns = all_df[all_df['row_type'].str.lower() == 'e3t'][['cmp1', 'cmp2', 'cmp3', 'val']].values.astype(int) - 1
    pts = all_df[all_df['row_type'].str.lower() == 'nd'][['cmp1', 'cmp2', 'cmp3']].values.astype(float)
    verts = pd.DataFrame(pts, columns=['x', 'y', 'z'])
    tris = pd.DataFrame(conns, columns=['v0', 'v1', 'v2', 'mat'])
    
    return tris, verts


def read_mesh2d(fpath):
    """
    Loads a .dat file containing mesh2d data corresponding to a 3dm mesh.

    Parameters
    ----------

    fpath: str
        Path to .dat file

    Returns
    -------

    dfs: dict(int: DataFrame)
        A dictionary of dataframes indexed by time.
    """
    attrs = {}
    with open(fpath, 'r') as f:
        dataset = f.readline()
        if not dataset.startswith('DATASET'):
            raise ValueError('Expected DATASET file, cannot read data.')
        objtype = f.readline()
        if not objtype.startswith('OBJTYPE "mesh2d"'):
            raise ValueError('Expected "mesh2d" OBJTYPE, cannot read data.')
        _ = f.readline()
        nd, nc = f.readline(), f.readline()
        name = f.readline()[6:-2]
        unit = f.readline()
    df = pd.read_table(fpath, delim_whitespace=True,
                       header=None, skiprows=7, names=[0, 1, 2]).iloc[:-1]
    ts_index = np.where(df[0]=='TS')[0]
    indexes = [df.iloc[idx, 2] for idx in ts_index]
    dfs = {}
    for time, tdf in zip(indexes, np.split(df, ts_index)[1:]):
        tdf = tdf.iloc[1:].astype(np.float64).dropna(axis=1, how='all')
        if len(tdf.columns) == 1:
            tdf.columns = [name]
        else:
            tdf.columns = [name+'_%d' % c for c in range(len(tdf.columns))]
        dfs[time] = tdf.reset_index(drop=True)
    return dfs


def save_shapefile(cdsdata, path, template):
    """
    Accepts bokeh ColumnDataSource data and saves it as a shapefile,
    using an existing template to determine the required schema.
    """
    collection = fiona.open(template)
    arrays = [np.column_stack([xs, ys]) for xs, ys in zip(cdsdata['xs'], cdsdata['ys'])]
    polys = gv.Polygons(arrays, crs=ccrs.GOOGLE_MERCATOR)
    projected = gv.operation.project_path(polys, projection=ccrs.PlateCarree())
    data = [list(map(tuple, arr)) for arr in projected.split(datatype='array')]
    shape_data = list(collection.items())[0][1]
    shape_data['geometry']['coordinates'] = data
    with fiona.open(path, 'w', collection.driver, collection.schema, collection.crs) as c:
        c.write(shape_data)

