from typing import Any

class ValidationRule:
    def __init__(self, rule: str, modifier: str = None, key:str|None=None,  value: Any=None):
        self.rule = rule
        self.modifier = modifier
        self.value = value

    def validate(self):
        from ..validation import Validator
        Validator.of().validate(
            f"{self.rule}:{self.modifier}",
        )


