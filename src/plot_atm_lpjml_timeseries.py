from pathlib import Path
import xarray as xr
import numpy as np

freezing_point = 273.15 # Kelvin

root = Path("/home/tienyiao/tienyiao_poem/projects/POEM_playground/add_flux_q_forcing")
output_dir = Path("figures")

output_dir.mkdir(exist_ok=True, parents=True)
casenames = [
    "control",
]

data_directories = {
    casename : root / f"{casename}/history" 
    for casename in casenames
}

control_casename = "control"

plotting_variables = [
#    ("atm", "t_ref"),
#    ("atm", "q_ref"),
#    ("atm", "sphum_surf"),
#    ("atm", "wind"),
    ("flx", "evap", 86400*30, "mm/month"),
    ("flxlnd", "evap_land", 86400*30, "mm/month"),
    ("lpjml", "evap1", 86400*30, "mm/month"),
#    ("lpjml", "mgpp"),
#    ("lpjml", "vegc"),
]

data = dict()

skip_years = 10
#lat_rng = [-2, 12]
#lon_rng = [360-82, 360-46]

lat_rng = [-16, -2]
lon_rng = [360-70, 360-50]

# load data
for casename in casenames:
    
    try:    

        data_directory = data_directories[casename]
        lpjml_data_directory = data_directory / "output_20220101_converted" 

        path_str = str(data_directory / "*.atmos_month.nc")

        print(f"Loading: {path_str:s}")
        ds_atm = xr.open_mfdataset(path_str, decode_times=False)
        ds_atm = ds_atm.where(
              (ds_atm.coords["lat"] > lat_rng[0]) & (ds_atm.coords["lat"] < lat_rng[1])
            & (ds_atm.coords["lon"] > lon_rng[0]) & (ds_atm.coords["lon"] < lon_rng[1])
        ).weighted(np.cos(ds_atm.coords["lat"]*np.pi/180)).mean(dim=["lat", "lon"])
        print(ds_atm)
 
        path_str = str(data_directory / "*.flux_month.nc")
        print(f"Loading: {path_str:s}")
        ds_flx = xr.open_mfdataset(path_str, decode_times=False)
        ds_flx = ds_flx.where(
              (ds_flx.coords["lat"] > lat_rng[0]) & (ds_flx.coords["lat"] < lat_rng[1])
            & (ds_flx.coords["lon"] > lon_rng[0]) & (ds_flx.coords["lon"] < lon_rng[1])
        ).weighted(np.cos(ds_flx.coords["lat"]*np.pi/180)).mean(dim=["lat", "lon"])
        print(ds_flx)
 
        path_str = str(data_directory / "*.flux_month_land.nc")
        print(f"Loading: {path_str:s}")
        ds_flxlnd = xr.open_mfdataset(path_str, decode_times=False)
        ds_flxlnd = ds_flxlnd.where(
              (ds_flxlnd.coords["lat"] > lat_rng[0]) & (ds_flxlnd.coords["lat"] < lat_rng[1])
            & (ds_flxlnd.coords["lon"] > lon_rng[0]) & (ds_flxlnd.coords["lon"] < lon_rng[1])
        ).weighted(np.cos(ds_flxlnd.coords["lat"]*np.pi/180)).mean(dim=["lat", "lon"], skipna=True)
        print(ds_flxlnd)
        
        ds_lpjml = xr.open_mfdataset([
            lpjml_data_directory / f"{varname}.nc"
            for varname in [
                "evap1",
                "mswc1",
                "mswc2",
                "mgpp",
                "vegc",
                "fpc",
            ]
        ], decode_times=False)
        ds_lpjml = ds_lpjml.where(
              (ds_lpjml.coords["lat"] > lat_rng[0]) & (ds_lpjml.coords["lat"] < lat_rng[1])
            & (ds_lpjml.coords["lon"] % 360 > lon_rng[0]) & (ds_lpjml.coords["lon"] % 360 < lon_rng[1])
        ).weighted(np.cos(ds_lpjml.coords["lat"]*np.pi/180)).mean(dim=["lat", "lon"], skipna=True)
        sum_fpc = ds_lpjml["fpc"].isel()
        print(ds_lpjml)

        data[casename] = {
            'atm' : ds_atm,
            'flx' : ds_flx,
            'flxlnd' : ds_flxlnd,
            'lpjml' : ds_lpjml,
        }

    except Exception as e:
        print(f"Error: Cannot load {casename:s}.")
        print(str(e))
        raise e

print("Data loaded")
# plot time series
import matplotlib as mplt
mplt.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.transforms import blended_transform_factory

from datetime import datetime

colors = plt.colormaps["plasma"](np.linspace(0, 1, len(data.keys()) + 3))

fig, ax = plt.subplots(len(plotting_variables), 1, sharex=True, figsize=(6, len(plotting_variables)*3), squeeze=False)

ax_flattened = ax.flatten()

for j, (component, varname, factor, unit) in enumerate(plotting_variables):
    _ax = ax_flattened[j]
    for i, (case_name, _data) in enumerate(data.items()):
        da = _data[component][varname]
        timeseries = da.to_numpy() * factor
        t = np.arange(len(timeseries))
        print(t.shape)
        #if component == "lpjml" and varname[0] != "m": # annual
        #    t *= 12
        _ax.plot(t, timeseries, color=colors[i], label=case_name)
        if i == 0:
            _ax.set_ylabel(f"[{unit:s}]")
    _ax.set_title(f"({component}: {varname})")
        
fig.suptitle(f"Average range : longitude $ \\in [{lon_rng[0]:.1f}, {lon_rng[1]:.1f}] $, latitude $ \\in [{lat_rng[0]:.1f}, {lat_rng[1]:.1f}] $")
for _ax in ax_flattened:
    _ax.grid()
    _ax.legend()
    _ax.set_xlabel("Month")

for extension in ["png", "svg"]:
    output_file = output_dir / f"atm_lnd_diagnostic.{extension}"
    print(f"Write to file: {str(output_file)}")
    fig.savefig(output_file, dpi=200)

print("Showing figure")
plt.show()
