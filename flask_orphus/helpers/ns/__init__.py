from typing import TypeVar

T = TypeVar("T")


class dot_dict:
    """
    A simple dot-notation wrapper for Python dictionaries.
    """

    def __init__(self, data: T):
        self.data: T = data

    def __getattr__(self, name: str) -> T:
        if name in self.data:
            value = self.data[name]
            if isinstance(value, dict):
                return dot_dict(value)
            else:
                return value
        else:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


class ns:
    """
    A simple null-safe wrapper for Python objects.
    """

    def __init__(self, obj: T):
        self.obj: T = obj

    def __getattr__(self, name: str) -> T:
        if self.obj is None:
            return ns(None)
        else:
            if isinstance(self.obj, (dict,)):
                self.obj = dot_dict(self.obj)
            if isinstance(self.obj, (dot_dict,)):
                self.obj = self.obj
                attr = getattr(self.obj, name, None)
                if isinstance(attr, dot_dict):
                    return ns(attr.data)
                return ns(attr) if attr is not None else ns(None)
            attr = getattr(self.obj, name, None)
            return ns(attr) if attr is not None else ns(None)

    def __setattr__(self, name, value):
        if name != "obj":
            if hasattr(self, "obj"):
                if isinstance(self.obj, (dict,)):
                    self.obj[name] = value
                else:
                    setattr(self.obj, name, value)
            else:
                super().__setattr__(name, value)
        else:
            super().__setattr__(name, value)

    def __getitem__(self, key):
        if self.obj is None:
            return ns(None)
        else:
            attr = self.obj[key]
            return ns(attr) if attr is not None else ns(None)

    def __setitem__(self, key, value):
        if self.obj is not None:
            self.obj[key] = value

    def __call__(self, *args, **kwargs) -> T:
        if self.obj is None:
            return ns(None)
        else:
            return ns(self.obj(*args, **kwargs))

    def is_null(self) -> bool:
        return self.obj is None

    def unwrap(self) -> T:
        return self.obj

    def __repr__(self) -> str:
        return repr(self.obj) if self.obj is not None else 'None'