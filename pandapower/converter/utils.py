import numpy as np
import matplotlib.pyplot as plt





def set_tap_percent_and_degree_from_table(trafo, trafo_characteristic_table):
    for index, row in trafo.iterrows():
        if row.tap_dependency_table:
            tap_max = row["tap_max"]
            tap_neutral = row["tap_neutral"]
            id_characteristic_table = row["id_characteristic_table"]
            trafo_table = trafo_characteristic_table[trafo_characteristic_table['id_characteristic'] == id_characteristic_table]
            if np.allclose(trafo_table["voltage_ratio"], 1, 1e-6):
                _update_ideal_tap_changer(trafo, index, tap_max, tap_neutral, trafo_table)
                _check_ideal_and_update_type(trafo, index, trafo_table)
            elif np.all(trafo_table["angle_deg"] == 0):
                _update_longitudinal_regulator(trafo, index, tap_max, tap_neutral, trafo_table)
                _check_ratio_and_update_type(trafo, index, trafo_table)
            else:
                _update_ratio_tap_changer(trafo, index, tap_max, tap_neutral, trafo_table)
                _check_ratio_and_update_type(trafo, index, trafo_table)

def _check_ideal_and_update_type(trafo, index, trafo_table):
    n = trafo_table["step"].to_numpy() - trafo.loc[index, "tap_neutral"]
    if np.median(trafo_table["angle_deg"] - n * trafo.loc[index, "tap_step_degree"]) < 1e-5: # median bc. if most steps are good, but largest step in table is just off, still count it is ok representation
        trafo.loc[index, "tap_changer_type"] = "Ideal"
    else: # failed to write as table
        trafo.loc[index, "tap_changer_type"] = "Tabular" # TODO Check with Panos
        trafo.loc[index, "tap_step_degree"] = 0 # revert to a default

def _check_ratio_and_update_type(trafo, index, trafo_table):
    n = trafo_table["step"].to_numpy() - trafo.loc[index, "tap_neutral"]
    ratios_complex = 1 + n * 0.01 * trafo.loc[index, "tap_step_percent"] * np.exp(1j * np.deg2rad(trafo.loc[index, "tap_step_degree"]))
    ratios = np.abs(ratios_complex)
    angles = np.rad2deg(np.angle(ratios_complex))
    # if np.median(trafo_table["angle_deg"]- angles) < 1e-5 and np.median(trafo_table["voltage_ratio"] -  ratios) < 1e-5:
    if np.allclose(trafo_table["angle_deg"], angles,  1e-5) and np.allclose(trafo_table["voltage_ratio"] ,  ratios, 1e-5):
        trafo.loc[index, "tap_changer_type"] = "Ratio"
    else: # failed to write as table
        plt.scatter(trafo_table["step"],trafo_table["voltage_ratio"])
        plt.show()
        plt.scatter(trafo_table["step"], trafo_table["vk_percent"])
        plt.title(trafo.name[index])
        plt.xlabel("step")
        plt.ylabel("vk_percent")
        plt.show()
        plt.scatter(trafo_table["step"], trafo_table["vkr_percent"])
        plt.title(trafo.name[index])
        plt.xlabel("step")
        plt.ylabel("vkr_percent")
        plt.show()
        trafo.loc[index, "tap_changer_type"] = "Tabular" # TODO Check with Panos
        trafo.loc[index, "tap_step_degree"] = 0 # revert to a default
        trafo.loc[index, "tap_step_percent"] = 0  # revert to a default


def _update_ratio_tap_changer(trafo, index, tap_max, tap_neutral, trafo_table):
    if tap_max > tap_neutral:
        index_table = trafo_table["step"] == (tap_neutral + 1)
        alpha = trafo_table["angle_deg"][index_table].values[0]
        ratio = trafo_table["voltage_ratio"][index_table].values[0]
        trafo.loc[index, "tap_step_percent"] = 100 * np.sqrt(ratio ** 2 + 1 - 2 * ratio * np.cos(np.deg2rad(alpha)))
        trafo.loc[index, "tap_step_degree"] = np.rad2deg(np.arctan2(ratio * np.sin(np.deg2rad(alpha)), (ratio * np.cos(np.deg2rad(alpha)) - 1)))
    else:
        index_table = trafo_table["step"] == (tap_neutral - 1)
        alpha = trafo_table["angle_deg"][index_table].values[0]
        ratio = trafo_table["voltage_ratio"][index_table].values[0]
        trafo.loc[index, "tap_step_percent"] = 100 * np.sqrt(ratio ** 2 + 1 - 2 * ratio * np.cos(np.deg2rad(alpha)))
        trafo.loc[index, "tap_step_degree"] = - np.rad2deg(np.arctan2(ratio * np.sin(np.deg2rad(alpha)), (1 - ratio * np.cos(np.deg2rad(alpha)))))

def _update_longitudinal_regulator(trafo, index, tap_max, tap_neutral, trafo_table):
    trafo.loc[index, "tap_step_degree"] = 0
    if tap_max > tap_neutral:
        index_table = trafo_table["step"] == (tap_neutral + 1)
        tap_step_percent = 100 * (trafo_table["voltage_ratio"][index_table].values[0] - 1.)
    else:
        index_table = trafo_table["step"] == (tap_neutral - 1)
        tap_step_percent = 100 * (1. - trafo_table["voltage_ratio"][index_table].values[0])
    if not np.isclose(tap_step_percent, trafo.loc[index, "tap_step_percent"], 1e-6):
        trafo.loc[index, "tap_step_percent"] = tap_step_percent

def _update_ideal_tap_changer(trafo, index, tap_max, tap_neutral, trafo_table):
    trafo.loc[index, "tap_step_percent"] = 0
    if tap_max > tap_neutral:
        index_table = trafo_table["step"] == (tap_neutral + 1)
        tap_step_degree = trafo_table["angle_deg"][index_table].values[0]
    else:
        index_table = trafo_table["step"] == (tap_neutral - 1)
        tap_step_degree = -trafo_table["angle_deg"][index_table].values[0]
    trafo.loc[index, "tap_step_degree"] = tap_step_degree
