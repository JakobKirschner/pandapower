from numpy.ma.testutils import assert_equal, assert_almost_equal

from pandapower.converter.utils import set_tap_percent_and_degree_from_table

import pandapower as pp
import pandas as pd
import numpy as np

def trafo3w_net():
    net = pp.create_empty_network(sn_mva=5)
    b1 = pp.create_bus(net, 220)
    b2 = pp.create_bus(net, 30)
    b3 = pp.create_bus(net, 10)
    pp.create_ext_grid(net, b1, s_sc_max_mva=100., s_sc_min_mva=40., rx_min=0.1, rx_max=0.1)
    pp.create_load(net, b2, 25, 5)
    pp.create_load(net, b3, 25, 10)
    pp.create_transformer3w_from_parameters(net, hv_bus=b1, mv_bus=b2, lv_bus=b3, vn_hv_kv=222,
                                            vn_mv_kv=33, vn_lv_kv=11., sn_hv_mva=50,
                                            sn_mv_mva=30, sn_lv_mva=20, vk_hv_percent=11,
                                            vkr_hv_percent=1., vk_mv_percent=11,
                                            vkr_mv_percent=1., vk_lv_percent=11.,
                                            vkr_lv_percent=1., pfe_kw=10, i0_percent=0.2,
                                            tap_neutral=2, tap_max=2, tap_changer_type=None,
                                            tap_min=-2,
                                            )
    net.trafo3w["id_characteristic_table"] = 42
    net.trafo3w["tap_dependency_table"] = True
    net["trafo_characteristic_table"] = pd.DataFrame(
        {'id_characteristic': [42,42,42,42,42], 'step': [-2, -1, 0, 1, 2], 'voltage_ratio': [1, 1, 1, 1, 1],
         'angle_deg': [0, 0, 0, 0, 0], 'vk_percent': [2, 3, 4, 5, 6],
         'vkr_percent': [1.323, 1.324, 1.325, 1.326, 1.327], 'vk_hv_percent': np.nan, 'vkr_hv_percent': np.nan,
         'vk_mv_percent': np.nan, 'vkr_mv_percent': np.nan, 'vk_lv_percent': np.nan, 'vkr_lv_percent': np.nan})
    return net

def test_set_tap_percent_and_degree_from_table_ideal():
    net = trafo3w_net()
    alpha_deg = -1.23
    net["trafo_characteristic_table"]["angle_deg"] = net["trafo_characteristic_table"]["step"]*alpha_deg
    set_tap_percent_and_degree_from_table(net.trafo3w, net.trafo_characteristic_table)
    assert np.isclose(net.trafo3w["tap_step_degree"], alpha_deg, atol=1e-10)

def test_set_tap_percent_and_degree_from_table_ratio():
    net = trafo3w_net()
    for tap_neut in [-2,0,2]:
        net.trafo3w["tap_neutral"] = tap_neut
        for theta_deg in [-120,-60,0,60,120]:
            tap_step_percent = 1.26
            n = net["trafo_characteristic_table"]["step"].to_numpy()-net.trafo3w["tap_neutral"].to_numpy()
            ratio_complex = 1 + n*0.01*tap_step_percent*np.exp(1j*np.deg2rad(theta_deg))
            net["trafo_characteristic_table"]["voltage_ratio"] = np.abs(ratio_complex)
            net["trafo_characteristic_table"]["angle_deg"] = np.rad2deg(np.angle(ratio_complex))
            set_tap_percent_and_degree_from_table(net.trafo3w, net.trafo_characteristic_table)
            assert np.isclose(net.trafo3w["tap_step_degree"], theta_deg, atol=1e-10)

