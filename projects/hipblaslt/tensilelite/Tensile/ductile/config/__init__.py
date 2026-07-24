# Copyright (c) Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

from types import MappingProxyType

import copy
import os
import yaml


def _deep_update(base, override):
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_update(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def update(cfg):
    if not isinstance(cfg, dict):
        raise ValueError("configuration override must be a dictionary")
    return _deep_update(dict(DEFAULTS), cfg)


def load(path=None):
    if not path:
        defaults_path = os.path.join(os.path.dirname(__file__), "defaults.yaml")
        with open(defaults_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return update(cfg)


def populate(conf, name):
    section = conf[name]
    if "name" not in conf[name]:
        raise ValueError(f"missing 'name' field for section '{name}'")
    sel = conf[name]["name"]
    res = {"name": sel}
    if sel in section:
        res = res | section[sel]
    if "common" in section:
        res = res | section["common"]
    return res


DEFAULTS = MappingProxyType(load())
