from typing import Any, Callable, Dict, List, Optional, Union

from ..events import GenericEventArguments
from .choice_element import ChoiceElement
from .mixins.disableable_element import DisableableElement


class Toggle(ChoiceElement, DisableableElement):

    def __init__(self,
                 options: Union[List, Dict], *,
                 value: Any = None,
                 on_change: Optional[Callable[..., Any]] = None,
                 ) -> None:
        """Toggle

        The options can be specified as a list of values, or as a dictionary mapping values to labels.
        After manipulating the options, call `update()` to update the options in the UI.

        :param options: a list ['value1', ...] or dictionary `{'value1':'label1', ...}` specifying the options
        :param value: the initial value
        :param on_change: callback to execute when selection changes
        """
        super().__init__(tag='q-btn-toggle', options=options, value=value, on_change=on_change)

    def _event_args_to_value(self, e: GenericEventArguments) -> Any:
        assert isinstance(e.args, int)
        return self._values[e.args]

    def _value_to_model_value(self, value: Any) -> Any:
        return self._values.index(value) if value in self._values else None
