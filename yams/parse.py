import oyaml as yaml  # type: ignore
import os
import collections
from typing import Optional, Dict, Any


# ============== PARSING FUNCTIONS ======================


def check_item(val, d, key_path, keys=None, pops=None):
    """
    Checks if an item meets the requirements of the field's definition.
    """
    if "min" in d:
        assert val >= d["min"], f"{val} must be greater than {d['min']} [{key_path}]"
    if "max" in d:
        assert val <= d["max"], f"{val} must be less than {d['max']} [{key_path}]"
    if d["type"] == "int":
        assert isinstance(val, int), f"{val} must be an integer [{key_path}]"
    if d["type"] == "float":
        if isinstance(val, int):
            val = float(val)

        # avoid floating point errors by making numbers more reasonable
        val = round(val, 6)

        assert isinstance(val, float), f"{val} must be a float [{key_path}]"
    if d["type"] == "boolean":
        assert isinstance(val, bool), f"{val} must be a bool [{key_path}]"
    if d["type"] == "enum":
        if "values" in d:
            values = d["values"]
        elif "class" in d:
            values = pops[d["class"]]
        assert val in values, f"{val} not in {values} [{key_path}]"
    if d["type"] == "array":
        if "values" in d:
            values = d["values"]
        elif "class" in d:
            values = pops[d["class"]]
        assert isinstance(val, list), f"{val} must be an array [{key_path}]"
        assert all(x in values for x in val), f"{val} not in {values} [{key_path}]"
    if d["type"] == "keys":
        assert isinstance(val, list), f"{val} must be an array of keys [{key_path}]"
        assert all(x in keys for x in val), f"{keys} not in {keys} [{key_path}]"
    return val


def get_item(key, d, key_path, param, pops=None):
    """
    Get and check item from the params, falling back on the definitions default.
    """
    if key in param:
        val = param[key]
        return check_item(val, d, f"{key_path}", pops=pops)
    else:
        return d["default"]


def merge(d1, d2):
    """return new merged dict of dicts"""
    if isinstance(d1, collections.abc.Mapping) and isinstance(
        d2, collections.abc.Mapping
    ):
        for k, v in d1.items():
            if k in d2:
                d2[k] = merge(v, d2[k])
        d3 = d1.copy()
        d3.update(d2)
        return d3
    else:
        return d2


def get_bins(key, d, key_path, param, pops):
    """
    Get and validate a type == bin definition
    """
    if key not in param:
        return d["default"]

    bins = merge(d["default"], param[key])

    parsed_bins = {}
    for bin, val in bins.items():
        try:
            int(bin)
        except ValueError:
            print("Bins must be integers")
            raise

        for field, defn in d["fields"].items():
            assert field in val, f"{field} must be in {val} [{key_path}.{bin}]"
            val[field] = check_item(
                val[field], defn, f"{key_path}.{bin}.{field}", pops=pops
            )

        parsed_bins[int(bin)] = val

    return parsed_bins


def get_defn(key, d, key_path, param, pops):
    """
    Get and validate a type == definition definition
    """
    if key not in param or param[key] == {}:
        parsed = d["default"]
    else:
        parsed = param[key]

    # check definitions
    for k, val in parsed.items():
        for field, defn in d["fields"].items():
            if field not in val:
                if "default" in defn:
                    val[field] = defn["default"]
                else:
                    assert field in val, f"{field} must be in {val} [{key_path}]"
            val[field] = check_item(
                val[field], defn, f"{key_path}.{field}", keys=parsed.keys(), pops=pops
            )

    return parsed


def parse_params(defs, params, key_path, pops):
    """
    Recursively parse the passed params, using the definitions to validate
    and provide defaults.
    """
    parsed = {}
    # params is a scalar, return it
    if not isinstance(params, dict):
        return params

    # handles case of bin as direct default item
    if "default" in defs:
        if defs["type"] == "bin":
            return get_bins("dummy", defs, key_path, {"dummy": params}, pops)
        elif defs["type"] == "definition":
            return get_defn("dummy", defs, key_path, {"dummy": params}, pops)

    for k, v in defs.items():
        # assumes all v are dicts, as otherwise it would have returned
        if "default" in v:
            if v["type"] == "sub-dict":
                parsed[k] = {}
                field = v["keys"][0]
                for val in pops[field]:
                    parsed[k][val] = parse_params(
                        v["default"],
                        params.get(k, {}).get(val, {}),
                        f"{key_path}.{k}.{val}",
                        pops,
                    )

                    if len(v["keys"]) > 1:
                        field2 = v["keys"][1]
                        for val2 in pops[field2]:
                            parsed[k][val][val2] = parse_params(
                                v["default"],
                                params.get(k, {}).get(val, {}).get(val2, {}),
                                f"{key_path}.{k}.{val}.{val2}",
                                pops,
                            )

            elif v["type"] == "bin":
                parsed[k] = get_bins(k, v, f"{key_path}.{k}", params, pops)
            elif v["type"] == "definition":
                parsed[k] = get_defn(k, v, f"{key_path}.{k}", params, pops)
            else:
                parsed[k] = get_item(k, v, f"{key_path}.{k}", params, pops)
        else:
            parsed[k] = parse_params(v, params.get(k, {}), f"{key_path}.{k}", pops)

    return parsed


def parse_classes(defs, params):
    """
    Parse the classes definition first as it is needed in parsing the full params.
    """
    if "classes" in defs:
        return parse_params(defs["classes"], params.get("classes", {}), "", {})
    else:
        return {}


def build_yaml(path):
    """
    Read in a yaml or folder of yamls into a dictionary.
    """
    yml = {}
    if os.path.isdir(path):
        for file in os.listdir(path):
            if ".yml" in file or ".yaml" in file:
                with open(os.path.join(path, file)) as f:
                    this_yml = yaml.safe_load(f)
                    yml.update(this_yml)
    else:
        with open(path) as f:
            assert ".yml" in path or ".yaml" in path
            this_yml = yaml.safe_load(f)
            yml.update(this_yml)

    return yml


def warn_unused_params(parsed, params, key_path):
    """
    Compare the original params to what was parsed and print warnings for any original
    params that are unused in the final parsed parasms.
    """
    # both values, return
    count = 0

    if not isinstance(parsed, dict) and not isinstance(params, dict):
        return count
    # params has keys, parsed doesn't
    elif not isinstance(parsed, dict):
        print(f"[{key_path}] has unused params: {params}")
        count += 1
        return count
    # parsed has keys, params doesn't
    elif not isinstance(params, dict):
        print(f"[{key_path}] has sub-keys, got unused params: {params}")
        count += 1
        return count

    for k, v in params.items():
        if k in parsed:
            count += warn_unused_params(parsed[k], params[k], f"{key_path}.{k}")
        else:
            print(f"[{key_path}.{k}] is unused")
            count += 1

    return count


def create_params(
    defn_path: str,
    *param_paths,
    error_on_unused: bool = False,
    out_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Entry function - given the path to the parameter definitions and files, parse and create a params dictionary.

    The defn_path and param_paths can be either a single yaml file, or a directory containing yaml files.

    args:
        defn_path: path to the parameter definitions
        *param_paths: paths to parameter files. The files will be merged in the passed order so that item 'a' in the first params will be overwritten by item 'a' in the second params.
        out_path: path to directory where computed params will be saved if passed
        error_on_unused: throw a hard error if there are unused parameters, otherwise warnings are only printed

    returns:
        computed/validated model paramters with defaults filled in where needed
    """
    defs = build_yaml(defn_path)

    params: Dict[str, Any] = {}
    for param_path in param_paths:
        cur_params = build_yaml(param_path)
        params = merge(params, cur_params)

    classes = parse_classes(defs, params)
    parsed = parse_params(defs, params, "", classes)

    if out_path is not None:
        with open(out_path, "w") as f:
            yaml.dump(parsed, f)

    print("\nChecking for unused parameters...")
    num_unused = warn_unused_params(parsed, params, "")
    print(f"{num_unused} unused parameters found")
    if error_on_unused:
        assert (
            num_unused == 0
        ), "There are unused parameters passed to the parser (see print statements)"

    return parsed
