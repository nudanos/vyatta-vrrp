import copy

import pytest

from pytest_lazy_fixtures import lf
import vyatta.vrrp_vci.keepalived.util as util


class TestKeepalivedUtils:

    def test_get_hello_sources_no_hellos(
            self, simple_config):
        expected = []
        assert util.get_hello_sources(simple_config) == expected

    def test_get_hello_sources(
            self, simple_config, interface_yang_name,
            dataplane_yang_name, vrrp_yang_name):
        expected = [
            [
                "10.1.1.1",
                "interfaces dataplane dp0p1s1 vrrp vrrp-group 1" +
                " hello-source-address 10.1.1.1"
            ]
        ]
        intf = simple_config[interface_yang_name][dataplane_yang_name][0]
        intf[vrrp_yang_name]["vrrp-group"][0]["hello-source-address"] = \
            "10.1.1.1"
        result = util.get_hello_sources(simple_config)
        assert expected == result

    def test_get_hello_sources_vifs(
            self, simple_config, interface_yang_name,
            dataplane_yang_name, vrrp_yang_name, generic_group):
        vif_config = copy.deepcopy(simple_config)
        expected = [
            [
                "10.1.1.1",
                "interfaces dataplane dp0p1s1 vif 10 vrrp vrrp-group 1" +
                " hello-source-address 10.1.1.1"
            ]
        ]
        del vif_config[interface_yang_name][dataplane_yang_name]
        vif_config[interface_yang_name]["vif"] = [
            {"tagnode": "dp0p1s1.10",
             vrrp_yang_name: {"vrrp-group": [copy.deepcopy(generic_group)]}}
        ]
        intf = vif_config[interface_yang_name]["vif"][0]
        intf[vrrp_yang_name]["vrrp-group"][0]["hello-source-address"] = \
            "10.1.1.1"
        result = util.get_hello_sources(vif_config)
        assert expected == result

    @pytest.mark.parametrize(
        "expected,address,fakes",
        [
            (True, "127.0.0.1", lf("socket_fakes")),
            (True, "::1", lf("socket_fakes")),
            (False, "10.1.1.1", lf("socket_fakes")),
        ],
        ids=[
            "ipv4", "ipv6", "No configured"
        ]
    )
    def test_is_local_address(self, expected, address, fakes):
        assert util.is_local_address(address) == expected

    @pytest.mark.parametrize(
        "expected,config",
        [
            (
                False,
                lf("simple_config")
            ),
            (
                True,
                lf("complex_config")
            ),
        ],
        ids=[
            "no", "yes"
        ]
    )
    def test_is_rfc_compat_configured(
            self, expected, config):
        assert util.is_rfc_compat_configured(config) == expected

    @pytest.mark.parametrize(
        "expected,hypervisor",
        [
            (False,
             lf("mock_show_version_rpc_no_hypervisor")),
            (False, lf("mock_show_version_rpc_kvm")),
            (True, lf("mock_show_version_rpc_vmware")),
        ],
        ids=[
            "Baremetal", "KVM", "VMWare"
        ]
    )
    def test_running_on_vmware(
            self, expected, hypervisor):
        assert util.running_on_vmware() == expected

    def test_sanitize_vrrp_config_one_configured(self,
                                                 simple_config):
        assert util.sanitize_vrrp_config(simple_config) == simple_config
        assert util.sanitize_vrrp_config(simple_config) is not simple_config

    @pytest.mark.parametrize(
        "test_value,expected_value",
        [
            (lf("no_vrrp_config"),
             lf("top_level_dictionary")),
            (lf("simple_multi_intf_same_type_config"),
             lf("simple_config")),
            (lf("simple_multi_intf_differing_type_config"),
             lf(
                 "simple_multi_intf_differing_type_config_sanitized")
             ),
            (lf("simple_dataplane_vif_config"),
             lf("simple_config")),
            (lf("simple_dataplane_vif_with_vrrp_config"),
             lf("simple_dataplane_vif_sanitized_config")),
            (lf("simple_multi_intf_type_vif_config"),
             lf(
                 "simple_multi_intf_type_vif_sanitized_config")
             ),
            (lf("switch_config_not_being_applied"),
             lf(
                 "expected_switch_config_not_being_applied")
             ),
        ],
        ids=[
            "No configured groups",
            "Two interfaces, one with and one without config",
            "Two types of interface with VRRP config",
            "Parent with config, vif without",
            "Move vif dataplane",
            "Move bonding and dataplane vif",
            "Switch vif",
        ]
    )
    def test_sanitize_vrrp_config(
            self, test_value, expected_value):
        assert test_value != expected_value
        assert util.sanitize_vrrp_config(test_value) == expected_value

    @pytest.mark.parametrize(
        "file_contents,search_string,expected",
        [
            (
                lf("autogeneration_string"),
                "global_defs",
                [6]
            ),
            (
                lf("autogeneration_string"),
                "vrrp_instance",
                []
            ),
            (
                lf("simple_keepalived_config"),
                "vrrp_instance",
                [14]
            ),
            (
                lf("multiple_group_keepalived_config"),
                "vrrp_instance",
                [14, 27]
            ),
        ],
        ids=[
            "Global defs", "No instances", "Single instance",
            "Multiple instances"
        ]
    )
    def test_get_config_indexes_list_autogen(
            self, file_contents, search_string, expected):
        result = util.get_config_indexes(
            file_contents.splitlines(), search_string)
        assert result == expected

    @pytest.mark.parametrize(
        "config_string,start_index,expected_block",
        [
            (
                lf("autogeneration_string"),
                [6],
                lf("autogeneration_config_block"),
            ),
            (
                lf("autogeneration_string"),
                [],
                [],
            ),
            (
                lf("simple_keepalived_config"),
                [14],
                lf("simple_keepalived_config_block"),
            ),
            (
                lf("multiple_group_keepalived_config"),
                [14, 27],
                lf("multiple_group_keepalived_config_block"),
            ),
        ],
        ids=[
            "Global defs", "No instances", "One instance",
            "Multiple instances"
        ]
    )
    def test_get_config_blocks(
            self, config_string, start_index, expected_block):
        assert util.get_config_blocks(
            config_string.splitlines(), start_index
        ) == expected_block

    @pytest.mark.parametrize(
        "config_list,search_string,expected",
        [
            (
                lf("autogeneration_config_block"),
                "snmp_socket",
                {"Type": str, "Value": "tcp:localhost:705:1"},
            ),
            (
                lf("autogeneration_config_block"),
                "enable_dbus",
                {"Type": list, "Value": [None]},
            ),
            (
                lf("multiple_group_keepalived_config_block"),
                "state",
                {"Type": str, "Value": "BACKUP"},
            ),
        ],
        ids=[
            "Autogen SNMP defined",
            "Autogen presence defined",
            "Multiple config blocks"
        ]
    )
    def test_find_value_in_config_blocks_value_exists(
            self, config_list, search_string, expected):
        for block in config_list:
            assert isinstance(
                util.find_config_value(block, search_string),
                expected["Type"]
            )
            assert util.find_config_value(block, search_string) \
                == expected["Value"]

    @pytest.mark.parametrize(
        "config_list,search_string,expected",
        [
            (
                lf("autogeneration_config_block"),
                "garp",
                {"Name": "MISSING", "Value": "NOTFOUND"},
            ),
            (
                lf("complex_keepalived_config_block"),
                "preempt",
                {"Name": "MISSING", "Value": "NOTFOUND"},
            ),
        ],
        ids=[
            "Autogen undefined key", "Overlapping substring",
        ]
    )
    def test_find_value_in_config_blocks_value_doesnt_exist(
            self, config_list, search_string, expected):
        for block in config_list:
            with pytest.raises(ValueError):
                util.find_config_value(block, search_string)

    @pytest.mark.parametrize(
        "intf_name,intf_list,intf_index",
        [
            (
                "dp0p1s1",
                lf("search_empty_dataplane_list"),
                0
            ),
            (
                "dp0p1s1",
                lf("search_dataplane_list"),
                0
            ),
            (
                "dp0p1s2",
                lf("search_dataplane_list"),
                1
            ),
        ],
        ids=[
            "Empty interface list", "Group in interface list",
            "Group not in interface list"
        ]
    )
    def test_find_interface_in_yang(
            self, intf_name, intf_list, intf_index):
        assert util.find_interface_in_yang_repr(
            intf_name, "", intf_list) in intf_list
        assert util.find_interface_in_yang_repr(
            intf_name, "", intf_list) is intf_list[intf_index]

    @pytest.mark.parametrize(
        "intf_name,vif_number,intf_list,intf_index,vif_index",
        [
            (
                "dp0p1s1",
                "10",
                lf("search_empty_dataplane_list"),
                0, 0
            ),
            (
                "dp0p1s1",
                "10",
                lf("search_dataplane_list"),
                0, 0
            ),
            (
                "dp0p1s1",
                "20",
                lf("search_vif_dataplane_list"),
                0, 1
            ),
            (
                "dp0p1s1",
                "10",
                lf(
                    "search_vif_dataplane_list_multiple_vrrp_groups"
                ),
                0, 0
            ),
        ],
        ids=[
            "interface doesnt exist, vif doesn't exist",
            "interface exists, vif doesn't exist",
            "interface exists, multiple vifs exist",
            "interface exists, vif exists with multiple VRRP groups"
        ]
    )
    def test_find_interface_in_yang_for_vifs(
            self, intf_name, vif_number, intf_list, intf_index, vif_index):
        assert util.find_interface_in_yang_repr(
            intf_name, vif_number, intf_list) in intf_list[intf_index]["vif"]
        assert util.find_interface_in_yang_repr(
            intf_name, vif_number, intf_list) is \
            intf_list[intf_index]["vif"][vif_index]

    @pytest.mark.parametrize(
        "intf_name,yang_name,common_name",
        [
            (
                "dp0bond1",
                lf("bonding_yang_name"),
                "bonding"
            ),
            (
                "sw0",
                lf("switch_yang_name"),
                "switch"
            ),
            (
                "dp0p1s1",
                lf("dataplane_yang_name"),
                "dataplane"
            ),
        ],
        ids=[
            "Bonding", "switch", "dataplane"
        ]
    )
    def test_intf_name_to_type(self, intf_name, yang_name, common_name):
        assert util.intf_name_to_type(intf_name)[0] == yang_name
        assert util.intf_name_to_type(intf_name)[1].name == common_name

    def test_intf_name_to_type_unknown_type(self):
        with pytest.raises(ValueError):
            util.intf_name_to_type("dp0p")

    @pytest.mark.parametrize(
        "time_delta,expected",
        [
            ("3", "3s"), ("60", "1m0s"), ("70", "1m10s"),
            ("3600", "1h0s"), ("3659", "1h59s"), ("3661", "1h1m1s"),
            ("86400", "1d0s"), ("190800", "2d5h0s"), ("828222", "1w2d14h3m42s")
        ],
        ids=[
            "Seconds", "Minute", "Minutes and seconds",
            "Hour", "Hour and seconds", "Hour, minute, and seconds",
            "Day", "Days and hours", "Weeks, days, hours, minutes, and seconds"
        ]
    )
    def test_elapsed_time(self, time_delta, expected):
        assert util.elapsed_time(time_delta) == expected
