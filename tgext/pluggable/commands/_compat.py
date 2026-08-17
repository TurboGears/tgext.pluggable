import re


def distribution_name(name):
    return re.sub(r'[^A-Za-z0-9.]+', '-', name)
