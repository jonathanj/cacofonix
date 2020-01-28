import yaml
from yaml.representer import SafeRepresenter
from collections import OrderedDict


class literal_str(str):
    pass


def change_style(style, representer):
    """
    Change the style of a particular YAML representer.
    """
    def new_representer(dumper, data):
        scalar = representer(dumper, data)
        scalar.style = style
        return scalar
    return new_representer


represent_literal_str = change_style('|', SafeRepresenter.represent_str)
yaml.add_representer(literal_str, represent_literal_str)

# Parse YAML mappings as OrderedDict, because we care about that sometimes.
yaml.add_representer(
    OrderedDict,
    lambda dumper, data: dumper.represent_dict(data.items()))
yaml.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    lambda loader, node: OrderedDict(loader.construct_pairs(node)))


def load(fd):
    """
    Load a YAML file.
    """
    return yaml.load(fd, Loader=yaml.FullLoader)


def dump(data):
    """
    Dump a YAML file.
    """
    return yaml.dump(data)
