import numpy as np
import xarray as xr
import cftime

days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
month_bounds = np.array([0.0, *np.cumsum(days_in_month)])
middle_of_months = (month_bounds[1:] + month_bounds[:-1] ) / 2

# Load the dataset
ds = xr.open_dataset("0020020101.flux_month_land.nc")

ref_array = ds["evap_land"]

lat = ds.coords["lat"].to_numpy()
lon = ds.coords["lon"].to_numpy()

llat, llon = np.meshgrid(lat, lon, indexing="ij")
if_in_region_of_interest = ( llat > -15 ) & (llat < 13) & ( llon > (-85 % 360)) & ( llon < (-30 % 360))

flux_q_scale   = np.ones_like(ref_array)
flux_q_forcing = np.zeros_like(ref_array)

water_density = 1e3 # kg/m^3
casename = "uniform"

months = None
if casename == "dry_season":
    months = [7, 8, 9]
elif casename == "uniform":
    months = list(range(1, 13))


for m in range(12):
    month = m + 1
    if month in months:
        flux_q_forcing[m, :, :] = np.where( 
            if_in_region_of_interest,
            1e-3 / (30*86400.0) * water_density,  # equivalent to evaporation of 1 mm per 30 days
            0.0,
        )

fill_value = 1e20

data_vars = {
    "flux_q_scale" : (("time", "lat", "lon"), flux_q_scale, dict(
        units = "1",
        missing_value = fill_value,
        _FillValue = fill_value,
    )),
    "flux_q_forcing" : (("time", "lat", "lon"), flux_q_forcing, dict(
        units = "kg/m^2/s",
        missing_value = fill_value,
        _FillValue = fill_value,
    )),
}

coords = {
    "time" : (("time"), middle_of_months, dict(
        units = 'days since 0001-01-01',
        calendar = 'noleap',
        modulo = ' ',
        axis = "T",
    )),
    "lon" : (("lon",), ds.coords["lon"].to_numpy(), dict(
        long_name = "longitude",
        units = "degrees_east",
        axis = "X",
    )),
    "lat" : (("lat",), ds.coords["lat"].to_numpy(), dict(
        long_name = "latitude",
        units = "degrees_north",
        modulo = ' ',
        axis = "Y",
    )),
}
    
ds_out = xr.Dataset(
    data_vars = data_vars,
    coords = coords,
)


ds_out.to_netcdf(f"pik_surface_flux_modification-{casename:s}.nc", unlimited_dims="time")
