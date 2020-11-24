import pytest
import os
import oyaml as yaml

from paraml.parse import *


def_path = "tests/params/defs.yaml"


def test_create_params_merging():
    params = create_params(
        def_path, "tests/params/a.yaml", "tests/params/b", "tests/params/c.yaml"
    )

    assert "cat" in params["classes"]["animals"]
    assert params["demographics"]["cat"]["barn"]["age_bins"][1]["age"] == 3
    assert params["demographics"]["cat"]["barn"]["age_bins"][2]["age"] == 14
    assert params["demographics"]["cat"]["barn"]["color"] == "indigo"
    assert params["demographics"]["cat"]["barn"]["num"] == 2
    assert params["demographics"]["turtle"]["ocean"]["prob_happy"] == 0.95
    assert params["neighbors"]["blue_buddies"]["distance"] == 90


def test_create_params_error():
    # this params file has a bad value, this makes sure the correct key is included in the error message
    param_file_bad_val = "tests/params/a_error.yaml"
    with pytest.raises(AssertionError) as excinfo:
        create_params(def_path, param_file_bad_val)

    assert "[.demographics.turtle.ocean.prob_happy]" in str(excinfo.value)


def test_create_params_error_unused():
    param_file_bad_val = "tests/params/a_unused.yaml"
    with pytest.raises(AssertionError) as excinfo:
        create_params(def_path, param_file_bad_val, error_on_unused=True)

    assert "There are unused parameters passed to the parser" in str(excinfo.value)


def test_create_params_write_read(tmpdir):
    out_path = os.path.join(tmpdir, "params.yml")
    params = create_params(
        def_path,
        "tests/params/a.yaml",
        "tests/params/b",
        "tests/params/c.yaml",
        out_path=out_path,
    )

    read_params = build_yaml(out_path)

    assert params == read_params


def test_check_item_min_max():
    defs = {"min": 0, "max": 3, "type": "float"}
    key_path = "item.test"

    # happy case
    assert check_item(1.5, defs, key_path) == 1.5

    # type coerciion to float
    assert check_item(1, defs, key_path) == 1.0

    # below min
    with pytest.raises(AssertionError):
        check_item(-1.5, defs, key_path)

    # above max
    with pytest.raises(AssertionError):
        check_item(4.5, defs, key_path)


def test_check_item_int():
    defs = {"min": 0, "max": 3, "type": "int"}
    key_path = "item.test"

    # happy case
    assert check_item(1, defs, key_path) == 1

    # not int
    with pytest.raises(AssertionError):
        check_item(1.5, defs, key_path)


def test_check_item_boolean():
    defs = {"type": "boolean"}
    key_path = "item.test"

    # happy case
    assert check_item(True, defs, key_path) == True

    # not bool
    with pytest.raises(AssertionError):
        check_item(1, defs, key_path)


def test_check_item_enum():
    defs = {"type": "enum", "values": ["a", "b"]}
    key_path = "item.test"

    # happy case
    assert check_item("a", defs, key_path) == "a"

    # not bool
    with pytest.raises(AssertionError):
        check_item("c", defs, key_path)


def test_check_item_array():
    defs = {"type": "array", "values": ["a", "b"]}
    key_path = "item.test"

    # happy case
    assert check_item(["a", "b"], defs, key_path) == ["a", "b"]
    assert check_item([], defs, key_path) == []
    assert check_item(["b"], defs, key_path) == ["b"]

    # not in array
    with pytest.raises(AssertionError):
        check_item(["c"], defs, key_path)

    # some not in array
    with pytest.raises(AssertionError):
        check_item(["a", "c"], defs, key_path)


def test_check_item_keys():
    defs = {"type": "keys"}
    key_path = "item.test"

    # happy case
    assert check_item(["a", "b"], defs, key_path, keys=["a", "b"]) == ["a", "b"]
    assert check_item([], defs, key_path, keys=["a", "b"]) == []
    assert check_item(["b"], defs, key_path, keys=["a", "b"]) == ["b"]

    # not in array
    with pytest.raises(AssertionError):
        check_item(["c"], defs, key_path, keys=["a", "b"])

    # some not in array
    with pytest.raises(AssertionError):
        check_item(["a", "c"], defs, key_path, keys=["a", "b"])


def test_check_item_class_enum():
    defs = {"type": "enum", "class": "bond_types"}
    key_path = "item.test"

    nested_pops = {"bond_types": {"Inj": {"a": 1}, "Other": {"b": 2}}}
    flat_pops = {"bond_types": ["Inj", "Other"]}

    # happy case
    assert check_item("Inj", defs, key_path, pops=nested_pops) == "Inj"
    assert check_item("Inj", defs, key_path, pops=flat_pops) == "Inj"

    # not in array
    with pytest.raises(AssertionError):
        check_item("Junk", defs, key_path, pops=nested_pops)

    # some not in array
    with pytest.raises(AssertionError):
        check_item("Junk", defs, key_path, pops=flat_pops)


def test_check_item_class_array():
    defs = {"type": "array", "class": "bond_types"}
    key_path = "item.test"

    nested_pops = {"bond_types": {"Inj": {"a": 1}, "Other": {"b": 2}}}
    flat_pops = {"bond_types": ["Inj", "Other"]}

    # happy case
    assert check_item(["Inj"], defs, key_path, pops=nested_pops) == ["Inj"]
    assert check_item(["Inj"], defs, key_path, pops=flat_pops) == ["Inj"]

    # not in array
    with pytest.raises(AssertionError):
        check_item(["Junk"], defs, key_path, pops=nested_pops)

    # some not in array
    with pytest.raises(AssertionError):
        check_item(["Junk"], defs, key_path, pops=flat_pops)
