import matplotlib.pyplot as plt
import numpy as np
import fastf1
import fastf1.plotting

# Setup FastF1 styling and caching
fastf1.plotting.setup_mpl()
fastf1.Cache.configure(cache_dir='f1_cache')

# ---------------------------------------------------------
# 1. Load Session & Driver Laps
# ---------------------------------------------------------
YEAR = 2023
RACE = 'Monza'
SESSION_TYPE = 'Q'

session = fastf1.get_session(YEAR, RACE, SESSION_TYPE)
session.load()

driver_ref = 'VER'  # Reference driver (Baseline)
driver_comp = 'SAI' # Comparison driver

# Use updated pick_drivers method
lap_ref = session.laps.pick_drivers(driver_ref).pick_fastest()
lap_comp = session.laps.pick_drivers(driver_comp).pick_fastest()

tel_ref = lap_ref.get_telemetry().add_distance()
tel_comp = lap_comp.get_telemetry().add_distance()

# ---------------------------------------------------------
# 2. Distance Grid Interpolation
# ---------------------------------------------------------
max_distance = min(tel_ref['Distance'].max(), tel_comp['Distance'].max())
distance_grid = np.arange(0, max_distance, 1.0)

def interp(tel, channel):
    return np.interp(distance_grid, tel['Distance'], tel[channel])

speed_ref_ms = interp(tel_ref, 'Speed') / 3.6
speed_comp_ms = interp(tel_comp, 'Speed') / 3.6

throttle_ref = interp(tel_ref, 'Throttle')
throttle_comp = interp(tel_comp, 'Throttle')
brake_ref = interp(tel_ref, 'Brake')
brake_comp = interp(tel_comp, 'Brake')
gear_ref = interp(tel_ref, 'nGear')
gear_comp = interp(tel_comp, 'nGear')

# ---------------------------------------------------------
# 3. Accumulated Delta Time (dt = dx / v)
# ---------------------------------------------------------
dt_ref = 1.0 / speed_ref_ms
dt_comp = 1.0 / speed_comp_ms

time_ref = np.cumsum(dt_ref)
time_comp = np.cumsum(dt_comp)

delta_time = time_comp - time_ref

# ---------------------------------------------------------
# 4. Multi-Panel Telemetry Overlay
# ---------------------------------------------------------
# Use updated get_driver_color function
color_ref = fastf1.plotting.get_driver_color(driver_ref, session=session)
color_comp = fastf1.plotting.get_driver_color(driver_comp, session=session)

fig, axs = plt.subplots(
    4, 1, 
    figsize=(14, 10), 
    sharex=True, 
    gridspec_kw={'height_ratios': [1.5, 2, 1, 1]}
)

plt.subplots_adjust(hspace=0.08)

# Panel 1: Delta Time
axs[0].plot(distance_grid, delta_time, color='white', linewidth=1.8)
axs[0].axhline(0, color='gray', linestyle='--', alpha=0.6)
axs[0].fill_between(distance_grid, 0, delta_time, where=(delta_time >= 0), color=color_comp, alpha=0.3)
axs[0].fill_between(distance_grid, 0, delta_time, where=(delta_time < 0), color=color_ref, alpha=0.3)
axs[0].set_ylabel(f'Delta (s)\n<{driver_ref} | {driver_comp}>', fontsize=10)
axs[0].grid(True, linestyle=':', alpha=0.4)
axs[0].set_title(
    f"{YEAR} {RACE} {SESSION_TYPE} — Telemetry Comparison: {driver_ref} vs {driver_comp}", 
    fontsize=14, fontweight='bold', pad=12
)

# Panel 2: Speed (km/h)
axs[1].plot(distance_grid, speed_ref_ms * 3.6, color=color_ref, label=driver_ref, linewidth=1.5)
axs[1].plot(distance_grid, speed_comp_ms * 3.6, color=color_comp, label=driver_comp, linewidth=1.5)
axs[1].set_ylabel('Speed (km/h)', fontsize=10)
axs[1].legend(loc='upper right', frameon=True)
axs[1].grid(True, linestyle=':', alpha=0.4)

# Panel 3: Throttle & Brake
axs[2].plot(distance_grid, throttle_ref, color=color_ref, linewidth=1.2, alpha=0.9)
axs[2].plot(distance_grid, throttle_comp, color=color_comp, linewidth=1.2, alpha=0.9)
axs[2].plot(distance_grid, brake_ref * 100, color=color_ref, linestyle='--', linewidth=1.2, alpha=0.7)
axs[2].plot(distance_grid, brake_comp * 100, color=color_comp, linestyle='--', linewidth=1.2, alpha=0.7)
axs[2].set_ylabel('Throttle / Brake (%)', fontsize=10)
axs[2].grid(True, linestyle=':', alpha=0.4)

# Panel 4: Gear Selection
axs[3].plot(distance_grid, gear_ref, color=color_ref, linewidth=1.2, drawstyle='steps-post')
axs[3].plot(distance_grid, gear_comp, color=color_comp, linewidth=1.2, drawstyle='steps-post')
axs[3].set_ylabel('Gear', fontsize=10)
axs[3].set_xlabel('Distance (m)', fontsize=11)
axs[3].grid(True, linestyle=':', alpha=0.4)

for ax in axs:
    ax.tick_params(direction='in', top=True, right=True)

plt.tight_layout()

# Save output graphic
output_filename = f"outputs/{YEAR}_{RACE}_{driver_ref}_vs_{driver_comp}.png"
plt.savefig(output_filename, dpi=300)
print(f"Success! Plot saved to {output_filename}")
plt.show()
