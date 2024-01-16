from typing import Callable

class Provider:
    providers = []

    def load(self):
        for provider in self.providers:
            if not callable(provider):
                raise TypeError("Provider must be a callable object.")
            provider()


    def add(self, provider: Callable | list[Callable]):
        if isinstance(provider, list):
            for p in provider:
                if not callable(p):
                    raise TypeError("Provider must be a callable object.")
                else:
                    self.add(p)
            return self
        elif callable(provider):
            self.providers.append(provider)
            return self
        else:
            raise TypeError(f"Provider [] must be a callable object.")
