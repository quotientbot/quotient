from tortoise.exceptions import ValidationError
from tortoise.validators import Validator


class ValueRangeValidator(Validator):
    """
    A validator to validate whether the given value is in given range or not.
    """

    def __init__(self, _range: range):
        self._range = _range

    def __call__(self, value: int):
        if not value in self._range:
            raise ValidationError(f"The value must be a number between `{self._range.start}` and `{self._range.stop}`.")
