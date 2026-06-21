"""Tests des actions de vision (image/pixel) et OCR (dégradation propre)."""

from __future__ import annotations

from unittest.mock import MagicMock

from autoflow.core import conditions, registry
from autoflow.core.executor import Executor
from autoflow.models.workflow import Schedule, Workflow


def run_workflow(actions, inputs=None, windows=None, ocr=None, vision=None, settings=None):
    inputs = inputs or MagicMock()
    windows = windows or MagicMock()
    wf = Workflow(name="T", schedule=Schedule(mode="run_once"), actions=actions)
    ex = Executor(wf, inputs, windows, sleep_func=lambda _s: None, settings=settings)
    if ocr is not None or vision is not None:
        original = ex._make_context

        def patched():
            ctx = original()
            if ocr is not None:
                ctx["ocr"] = ocr
            if vision is not None:
                ctx["vision"] = vision
            return ctx

        ex._make_context = patched
    ex.run()
    return ex


def test_find_image_stocke_position():
    vision = MagicMock()
    vision.is_available.return_value = True
    vision.locate_center.return_value = (120, 80)
    action = registry.create_action("find_image", params={
        "image_path": "img.png", "var_name": "pos"})
    ex = run_workflow([action], vision=vision)
    assert ex.variables.get("pos") == "120,80"
    assert ex.variables.get("pos_x") == 120


def test_find_image_fallback_pyautogui_si_opencv_absent():
    inputs = MagicMock()
    inputs.locate_center.return_value = (5, 6)
    vision = MagicMock()
    vision.is_available.return_value = False
    action = registry.create_action("find_image", params={
        "image_path": "img.png", "var_name": "pos"})
    ex = run_workflow([action], inputs=inputs, vision=vision)
    inputs.locate_center.assert_called_once()
    assert ex.variables.get("pos") == "5,6"


def test_wait_for_pixel_trouve():
    inputs = MagicMock()
    inputs.pixel.return_value = (255, 255, 255)
    action = registry.create_action("wait_for_pixel", params={
        "x": 1, "y": 1, "color": "#ffffff", "tolerance": 0, "timeout": 1})
    wf = Workflow(name="T", schedule=Schedule(mode="run_once"), actions=[action])
    ex = Executor(wf, inputs, MagicMock(), sleep_func=lambda _s: None)
    ex.run()
    inputs.pixel.assert_called()


def test_read_text_degrade_si_tesseract_absent():
    ocr = MagicMock()
    ocr.is_available.return_value = False
    action = registry.create_action("read_text", params={"var_name": "txt"})
    ex = run_workflow([action], ocr=ocr)
    # Aucune exception, variable vide, et aucun appel à read_region.
    assert ex.variables.get("txt") == ""
    ocr.read_region.assert_not_called()


def test_read_text_ocr_disponible():
    ocr = MagicMock()
    ocr.is_available.return_value = True
    ocr.read_region.return_value = "Texte lu"
    action = registry.create_action("read_text", params={
        "var_name": "txt", "region": True, "x": 0, "y": 0, "width": 10, "height": 10})
    ex = run_workflow([action], ocr=ocr)
    assert ex.variables.get("txt") == "Texte lu"
    ocr.read_region.assert_called_once()


# -- Conditions vision/pixel ---------------------------------------------
def test_condition_pixel_color():
    inputs = MagicMock()
    inputs.pixel.return_value = (10, 20, 30)
    params = {"test": "pixel_color", "x": 0, "y": 0, "color": "#0a141e", "tolerance": 0}
    assert conditions.evaluate(params, inputs, MagicMock(), {}) is True


def test_condition_pixel_color_hors_tolerance():
    inputs = MagicMock()
    inputs.pixel.return_value = (200, 200, 200)
    params = {"test": "pixel_color", "x": 0, "y": 0, "color": "#000000", "tolerance": 10}
    assert conditions.evaluate(params, inputs, MagicMock(), {}) is False


def test_parse_color_formats():
    assert conditions._parse_color("#ff0000") == (255, 0, 0)
    assert conditions._parse_color("0,128,255") == (0, 128, 255)


def test_vision_backend_indisponible_sans_cv2(monkeypatch):
    import builtins

    from autoflow.core.vision import VisionBackend

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "cv2":
            raise ImportError("pas d'opencv")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    assert VisionBackend().is_available() is False
