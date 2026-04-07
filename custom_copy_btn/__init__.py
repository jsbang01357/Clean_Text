from pathlib import Path
from typing import Optional
import streamlit.components.v1 as components

frontend_dir = (Path(__file__).parent / "frontend").absolute()
_component_func = components.declare_component(
    "custom_copy_btn", path=str(frontend_dir)
)

def copy_to_clipboard(
    text: str,
    before_copy_label: str = "📋",
    after_copy_label: str = "✅",
    key: Optional[str] = None,
):
    component_value = _component_func(
        key=key,
        text=text,
        before_copy_label=before_copy_label,
        after_copy_label=after_copy_label,
    )
    return component_value
