from pathlib import Path
import xarray as xr
import numpy as np

freezing_point = 273.15 # Kelvin

root = Path("/home/tienyiao/tienyiao_poem/projects/POEM_playground/add_flux_q_forcing")
output_dir = Path("figures")

output_dir.mkdir(exist_ok=True, parents=True)
casenames = [
    "control",
    "increase_10mm_per_30day",
    "increase_20mm_per_30day",
    "increase_30mm_per_30day",
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
lat_rng = [-18, 0]
lon_rng = [290, 315]
# load data
for casename in casenames:
    
    try:    
        merge = []

        data_directory = data_directories[casename]
        path_str = str(data_directory / "*.atmos_month.nc")
        print(f"Loading: {path_str:s}")
        ds = xr.open_mfdataset(path_str, decode_times=False)
        ds = ds[["precip"]].where(
              (ds.coords["lat"] > lat_rng[0]) & (ds.coords["lat"] < lat_rng[1])
            & (ds.coords["lon"] > lon_rng[0]) & (ds.coords["lon"] < lon_rng[1])
        ).weighted(np.cos(ds.coords["lat"]*np.pi/180)).mean(dim=["lat", "lon"])
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
from matplotlib.transforms import blended_transform_factory

from datetime import datetime

colors = plt.colormaps["plasma"](np.linspace(0, 1, len(data.keys()) + 3))

fig, ax = plt.subplots(1, 1, sharex=True, figsize=(6, 4), squeeze=False)

ax_flattened = ax.flatten()

_ax = ax_flattened[0]
for i, (case_name, ds) in enumerate(data.items()):
    time_year = ds.coords["time"] / 365
    _data = ds["precip"].to_numpy() * 86400 * 30
    _ax.errorbar(x=np.arange(1, 13),
             y=_data.mean(axis=0), 
             yerr=_data.std(axis=0), 
             fmt='-o',          # Line with circular markers
             capsize=5,         # Adds horizontal 'caps' to the error bars
             color=colors[i],
             label=case_name,
    )
    #_ax.boxplot(ds["precip"].to_numpy(), label=case_name)

_ax.set_title("Precipitation rate")
fig.suptitle(f"Average range : longitude $ \\in [{lon_rng[0]:.1f}, {lon_rng[1]:.1f}] $, latitude $ \\in [{lat_rng[0]:.1f}, {lat_rng[1]:.1f}] $")
for _ax in ax_flattened:
    _ax.grid()
    _ax.legend()
    _ax.set_xlabel("Month")
    _ax.set_ylabel("[mm / 30 days]")

#timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#fig.text(0.5, 0.01, f"Generated on: {timestamp}", ha="center", fontsize=10, color='gray')
#fig.suptitle("CM2Mc TIPMIP runs diagnostic:\n$\\mathrm{CO}_2$ mixing ratio and global mean surface air temperature (GMSAT)")

for extension in ["png", "svg"]:
    output_file = output_dir / f"Precipitation_response.{extension}"
    print(f"Write to file: {str(output_file)}")
    fig.savefig(output_file, dpi=200)

print("Showing figure")
plt.show()
