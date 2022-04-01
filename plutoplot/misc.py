"""Miscellaneous tools"""

# functools.cached_property exists for Python >=3.8
# use own implementation for version before
try:
    from functools import cached_property
except ImportError:

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


class Slicer:
    """Helper class to create sliced subclass

    Takes a class to create and arbitrary keyword arguments to pass to the class.
    It then initializes the object when accessed with `slicer[:]`, and passes the
    slice as additional kwarg (with name `slice_`) to the class.
    """

    def __init__(self, SliceClass, **kwargs):
        self.SliceClass = SliceClass
        self.kwargs = kwargs

    def __getitem__(self, slice_):
        return self.SliceClass(slice_=slice_, **self.kwargs)
