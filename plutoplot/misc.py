def cached_property(func):
    def wrapper(self):
        cached_name = "_" + func.__name__
        try:
            return getattr(self, cached_name)
        except AttributeError:
            setattr(self, cached_name, func(self))
        return getattr(self, cached_name)
    return property(wrapper)
