from pathlib import Path
import argparse
import xarray as xr
import numpy as np

parser = argparse.ArgumentParser(description="Plot LPJmL evaporation maps from POEM cases with ERA5 as benchmark.")
parser.add_argument("--lat-min", type=float, default=-15.0, help="Southern boundary of the map extent (default: -15.0)")
parser.add_argument("--lat-max", type=float, default=13.0,  help="Northern boundary of the map extent (default: 13.0)")
parser.add_argument("--lon-min", type=float, default=-85.0, help="Western boundary of the map extent, -180–360 (default: -85.0)")
parser.add_argument("--lon-max", type=float, default=-30.0, help="Eastern boundary of the map extent, -180–360 (default: -30.0)")
parser.add_argument("--casenames", nargs="+", default=["articifial_wet_off", "articifial_wet_on"],
                    help="One or more POEM case names to plot (default: articifial_wet_off articifial_wet_on)")
parser.add_argument("--label", type=str, default="",
                    help="Region label shown in the plot title (e.g. south_amazon_land)")
parser.add_argument("--season", choices=["DJF", "MAM", "JJA", "SON", "ANNUAL"], default="JJA",
                    help="Season to average over; ANNUAL uses all 12 months (default: JJA)")
args = parser.parse_args()

SEASON_MONTHS = {"DJF": [12, 1, 2], "MAM": [3, 4, 5], "JJA": [6, 7, 8], "SON": [9, 10, 11],
                 "ANNUAL": list(range(1, 13))}

lat_rng = [args.lat_min, args.lat_max]
lon_rng = [args.lon_min % 360, args.lon_max % 360]
casenames = args.casenames
months = np.array(SEASON_MONTHS[args.season])

root = Path("./data")
output_dir = Path("figures/map")

output_dir.mkdir(exist_ok=True, parents=True)

data_directories = {
    casename : root / f"{casename}"
    for casename in casenames
}

data = dict()

# load era5
try:
    path_str = [
        "data/era5/data_stream-moda_stepType-avgad.nc",
        "data/era5/data_stream-moda_stepType-avgua.nc",
    ]
    print(f"Loading ERA5: {path_str}")
    ds_era5 = xr.merge([
        xr.open_dataset(_path).drop_vars("valid_time")
        for _path in path_str
    ])
    ds_era5 = ds_era5.coarsen(valid_time=12).construct(valid_time=("year", "month"))
except Exception as e:
    print(f"Error: Cannot load ERA5.")
    print(str(e))
    raise e

# load LPJmL evaporation data
for casename in casenames:
    try:
        data_directory = data_directories[casename] / "history"
        lpjml_data_directory = data_directory / "lpjml_output"
        evap_path = lpjml_data_directory / "evap1.nc"
        print(f"Loading: {evap_path}")
        ds = xr.open_dataset(evap_path, decode_times=False)
        ds = ds.coarsen(time=12).construct(time=("year", "month"))
        data[casename] = ds
    except Exception as e:
        print(f"Error: Cannot load {casename}.")
        print(str(e))

print("Data loaded")

# plot maps
import matplotlib as mplt
mplt.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import tool_fig_config
import cartopy.crs as ccrs

h = 3
w = h * (args.lon_max - args.lon_min) / (args.lat_max - args.lat_min)
nrow = 1
ncol = 1 + len(casenames)  # ERA5 + one per case

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

levels = np.linspace(0, 200, 11)

def plot_panel(_ax, lon, lat, data_2d, title):
    mappable = _ax.contourf(
        lon, lat, data_2d,
        levels=levels,
        cmap='YlGnBu',
        transform=map_transform,
        extend="both",
    )
    cax = tool_fig_config.addAxesNextToAxes(fig, _ax, "right", thickness=0.1, spacing=0.3,
                                             flag_ratio_thickness=False, flag_ratio_spacing=False)
    cb = plt.colorbar(mappable, cax=cax, orientation="vertical", pad=0.00)
    cb.ax.tick_params(axis='both', labelsize=12)
    cb.set_label("[mm / 30 days]")
    _ax.set_title(title)
    _ax.set_extent([args.lon_min, args.lon_max, args.lat_min, args.lat_max], crs=map_transform)
    _ax.coastlines()
    gl = _ax.gridlines(draw_labels=True, linewidth=0.5, color="gray", alpha=0.7, linestyle="--")
    gl.xlocator = mticker.MultipleLocator(30)
    gl.ylocator = mticker.MultipleLocator(30)
    gl.top_labels = False
    gl.right_labels = False

# ERA5 — left-most panel
# ERA5 `e` is m/day (negative convention), negate and convert to mm/month
era5_evap = -ds_era5["e"].isel(month=months-1).mean(dim=["year", "month"]) * 30 * 1000
era5_lat = ds_era5.coords["latitude"].to_numpy()
era5_lon = ds_era5.coords["longitude"].to_numpy()
plot_panel(ax_flattened[0], era5_lon, era5_lat, era5_evap, "ERA5")

# LPJmL cases — evap1 is in kg/m²/s, convert to mm/month
for i, (case_name, ds) in enumerate(data.items()):
    evap = ds["evap1"].isel(month=months-1).mean(dim=["year", "month"]) * 86400 * 30
    lat = ds.coords["lat"].to_numpy()
    lon = ds.coords["lon"].to_numpy()
    plot_panel(ax_flattened[1 + i], lon, lat, evap, case_name)

label_prefix = f"{args.label} — " if args.label else ""
fig.suptitle(f"{label_prefix}LPJmL Evaporation — {args.season}")

label_part = f"{args.label}_" if args.label else ""
for extension in ["png", "svg"]:
    output_file = output_dir / f"lpjml_evap_map_{label_part}{args.season}_lat{args.lat_min:.1f}to{args.lat_max:.1f}_lon{args.lon_min:.1f}to{args.lon_max:.1f}.{extension}"
    print(f"Write to file: {str(output_file)}")
    fig.savefig(output_file, dpi=200)

print("Showing figure")
plt.show()
