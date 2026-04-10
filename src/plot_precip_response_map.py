from pathlib import Path
import xarray as xr
import numpy as np

freezing_point = 273.15 # Kelvin

root = Path("/home/tienyiao/tienyiao_poem/projects/POEM_playground/add_flux_q_forcing")
output_dir = Path("figures")
lat_rng = [-15, 13]
lon_rng = [360-85, 360-30]

timeseries_lat_rng = [-18, 0]
timeseries_lon_rng = [290, 315]

months=np.array([7,8,9])

output_dir.mkdir(exist_ok=True, parents=True)
casenames = [
    "control",
    "increase_10mm_per_30day",
    "increase_20mm_per_30day",
    "increase_30mm_per_30day",
]

casenames = [
    "control",
    "increase_uniform_10mm_per_30day",
    "increase_uniform_20mm_per_30day",
    "increase_uniform_30mm_per_30day",
]


data_directories = {
    casename : root / f"{casename}/history" 
    for casename in casenames
}

control_casename = "control"

data = dict()

skip_years = 10
# load data
for casename in casenames:
    
    try:    
        merge = []

        data_directory = data_directories[casename]
        path_str = str(data_directory / "*.atmos_month.nc")
        print(f"Loading: {path_str:s}")
        ds = xr.open_mfdataset(path_str, decode_times=False)
        ds = ds.isel(time=slice(skip_years*12, None)).coarsen(time=12).construct(time=("year", "month"))
        print(ds)
        merge.append(ds)
        data[casename] = xr.merge(merge)
    except Exception as e:
        print(f"Error: Cannot load {casename:s}.")
        print(str(e))

print("Data loaded")
# plot time series
import matplotlib as mplt
mplt.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

import tool_fig_config
import cartopy.crs as ccrs
from datetime import datetime

w = 6
h = 3
nrow = 1
ncol = len(casenames)

figsize, gridspec_kw = tool_fig_config.calFigParams(
    w = w,
    h = h,
    wspace = 1.5,
    hspace = 0.5,
    w_left = 1.0,
    w_right = 1.5,
    h_bottom = 1.0,
    h_top = 1.0,
    ncol = ncol,
    nrow = nrow,
)

map_projection = ccrs.PlateCarree()
map_transform = ccrs.PlateCarree()
 
fig, ax = plt.subplots(
    nrow, ncol,
    figsize=figsize,
    subplot_kw=dict(projection=map_projection, aspect="auto"),
    gridspec_kw=gridspec_kw,
    constrained_layout=False,
    squeeze=False,
)

ax_flattened = ax.flatten()

ax_index = 0;

def add_patch(ax, lon_rng, lat_rng, color):
    ax.add_patch(mpatches.Rectangle(
        (lon_rng[0], lat_rng[0]), lon_rng[1] - lon_rng[0], lat_rng[1] - lat_rng[0],
        fill=False, color=color, linewidth=2, 
        transform=map_transform
    ))


for i, (case_name, ds) in enumerate(data.items()):
    _ax = ax_flattened[ax_index]; ax_index+=1
    _data = ds["precip"].isel(month=months-1).mean(dim=["year", "month"]) * 86400.0 * 30
    lat = ds.coords["lat"].to_numpy()
    lon = ds.coords["lon"].to_numpy()
    mappable = precip_contour = _ax.contourf(
        lon, lat, _data,
        levels = np.linspace(0, 500, 11),
        cmap='YlGnBu', 
        transform=map_transform,
        extend="both"
    ) 

    cax = tool_fig_config.addAxesNextToAxes(fig, _ax, "right", thickness=0.1, spacing=0.3, flag_ratio_thickness=False, flag_ratio_spacing=False)
    cb = plt.colorbar(mappable, cax=cax, orientation="vertical", pad=0.00)
    cb.ax.tick_params(axis='both', labelsize=12)
    cb.set_label("[mm / 30 days]")
    _ax.set_title(f"{case_name:s}")


    add_patch(_ax, lon_rng, lat_rng, color="red")
    add_patch(_ax, timeseries_lon_rng, timeseries_lat_rng, color="black")


for _ax in ax_flattened:
    _ax.coastlines()


fig.suptitle("Months: %s" % (', '.join(["%d" % m for m in months])))


for extension in ["png", "svg"]:
    output_file = output_dir / f"Precipitation_response_map_uniform.{extension}"
    print(f"Write to file: {str(output_file)}")
    fig.savefig(output_file, dpi=200)

print("Showing figure")
plt.show()
