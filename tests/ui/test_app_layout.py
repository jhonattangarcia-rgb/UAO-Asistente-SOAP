"""Smoke tests for the layout/order of app.py using AppTest.

These tests guard against regressions in the visual restructuring done for
the Supabase historial integration (specs/009-supabase-historial-ui): the
audio recorder now appears AFTER the two text input panels (and above the
generate button), and the two text input panels remain side by side in a
two-column layout.
"""

from __future__ import annotations

from streamlit.testing.v1 import AppTest


def _load_app() -> AppTest:
    at = AppTest.from_file("app.py")
    at.run(timeout=30)
    assert not at.exception
    return at


def _main_children(at: AppTest) -> list[object]:
    return list(at.main.children.values())


def _contains_type(element: object, type_name: str) -> bool:
    if type(element).__name__ == type_name:
        return True
    children = getattr(element, "children", None)
    if not children:
        return False
    return any(_contains_type(child, type_name) for child in children.values())


def _index_of_first_containing(children: list[object], type_name: str) -> int:
    for i, child in enumerate(children):
        if _contains_type(child, type_name):
            return i
    raise AssertionError(f"No element of type {type_name} found among {children}")


_EXPECTED_TEXT_AREA_COUNT = 2


def _count_text_areas(element: object) -> int:
    if type(element).__name__ == "TextArea":
        return 1
    children = getattr(element, "children", None)
    if not children:
        return 0
    return sum(_count_text_areas(child) for child in children.values())


def _index_of_text_area_columns_block(children: list[object]) -> int:
    for i, child in enumerate(children):
        if type(child).__name__ != "Block":
            continue
        columns = list(getattr(child, "children", {}).values())
        if len(columns) != _EXPECTED_TEXT_AREA_COUNT or not all(type(col).__name__ == "Column" for col in columns):
            continue
        text_areas = sum(_count_text_areas(col) for col in columns)
        if text_areas == _EXPECTED_TEXT_AREA_COUNT:
            return i
    raise AssertionError("No two-column block with two text areas found")


def test_recorder_component_appears_after_text_input_panels() -> None:
    at = _load_app()
    children = _main_children(at)
    recorder_index = _index_of_first_containing(children, "UnknownElement")
    text_inputs_index = _index_of_text_area_columns_block(children)
    assert recorder_index > text_inputs_index


def test_text_inputs_remain_in_two_columns() -> None:
    at = _load_app()
    labels = {text_area.label for text_area in at.text_area}
    assert any("EVOLUCI" in label.upper() for label in labels)
    assert any("CAMBIOS" in label.upper() for label in labels)
    _index_of_text_area_columns_block(_main_children(at))


def test_generate_button_present() -> None:
    at = _load_app()
    labels = [button.label for button in at.button]
    assert any("Generar" in label for label in labels)
