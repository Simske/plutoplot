"""Miscellaneous tools"""


def cached_property(func):
    """Cache class property decorator

    Caches attribute under `_attr_`.
    """

    def wrapper(self):
        cached_name = "_" + func.__name__
        try:
            return getattr(self, cached_name)
        except AttributeError:
            setattr(self, cached_name, func(self))
        return getattr(self, cached_name)

    return property(wrapper)
