from typing import Any

class ContainerBinding:
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __dict__(self):
        return {
            self.key: self.value
        }


class Container:
    @classmethod
    def make(self):
        obj = self()
        obj.container = dict()
        return obj

    def bind(self, value: Any | list[ContainerBinding], key=None):
        if isinstance(value, list):
            for v in value:
                if not isinstance(v, ContainerBinding):
                    raise TypeError("Value must be an instance of ContainerBinding.")
                self.bind(v)
            return self
        if isinstance(value, ContainerBinding):
            self.container.update(value.__dict__())
            return self
        else:
            if not key:
                raise ValueError("Key must be provided.")
            self.container[key] = value
            return self
        return self

    def all(self):
        return self.container

    def __getattr__(self, item: str):
        if item in self.all():
            return self.container[item]
        raise AttributeError(f"'Container' object has no attribute [{item}]")
