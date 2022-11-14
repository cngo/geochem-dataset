def not_empty_str(instance, attribute, value):
    if len(value.strip()) == 0:
        raise ValueError(f"'{attribute.name}' must be a non-empty string")


def not_negative_int(instance, attribute, value):
    if value < 0:
        raise ValueError(f"'{attribute.name}' must be a non-negative integer")


def gte_other_attrib(other_attrib_name):
    def _gte_other_attrib(instance, attribute, value):
        if value < getattr(instance, other_attrib_name):
            raise ValueError(f"'{attribute.name}' greater than or equal to '{other_attrib_name}'")

    return _gte_other_attrib


def valid_latitude(instance, attribute, value):
    if value < -90 or value > 90:
        raise ValueError(f"'{attribute.name}' must be a valid latitude between -90 and 90")


def valid_longitude(instance, attribute, value):
    if value < -180 or value > 180:
        raise ValueError(f"'{attribute.name}' must be a valid longitude between -180 and 180")


def other_attrib_given(other_attrib_name):
    def _other_attrib_given(instance, attribute, value):
        if getattr(instance, other_attrib_name, None) is None:
            raise ValueError(f"'{other_attrib_name}' must be given because '{attribute.name}' is given")

    return _other_attrib_given
