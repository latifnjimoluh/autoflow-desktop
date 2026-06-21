"""Tests des actions : round-trip de sérialisation et appels au backend."""

from __future__ import annotations

import pytest

from autoflow.core import registry


@pytest.mark.parametrize("type_name", [name for name, _ in registry.available_types()])
def test_round_trip_to_from_dict(type_name):
    """to_dict / from_dict doit reproduire une action identique."""
    action = registry.create_action(type_name, delay_after=0.5)
    data = action.to_dict()
    rebuilt = registry.action_from_dict(data)
    assert rebuilt.to_dict() == data
    assert rebuilt.type_name == type_name
    assert rebuilt.delay_after == 0.5


@pytest.mark.parametrize("type_name", [name for name, _ in registry.available_types()])
def test_summary_est_une_chaine(type_name):
    action = registry.create_action(type_name)
    assert isinstance(action.summary(), str)
    assert action.summary()


def test_click_appelle_backend(inputs, windows, context):
    action = registry.create_action("click", params={"x": 10, "y": 20, "button": "right", "clicks": 2})
    action.execute(inputs, windows, context)
    inputs.click.assert_called_once_with(x=10, y=20, button="right", clicks=2)


def test_click_position_actuelle(inputs, windows, context):
    action = registry.create_action("click", params={"use_current": True})
    action.execute(inputs, windows, context)
    inputs.click.assert_called_once_with(x=None, y=None, button="left", clicks=1)


def test_click_clics_invalides():
    action = registry.create_action("click", params={"clicks": 0})
    with pytest.raises(ValueError):
        action.validate()


def test_move_mouse(inputs, windows, context):
    action = registry.create_action("move_mouse", params={"x": 5, "y": 6, "duration": 0.3})
    action.execute(inputs, windows, context)
    inputs.move_to.assert_called_once_with(5, 6, duration=0.3)


def test_drag(inputs, windows, context):
    action = registry.create_action("drag", params={"x1": 1, "y1": 2, "x2": 3, "y2": 4, "duration": 0.2})
    action.execute(inputs, windows, context)
    inputs.drag_to.assert_called_once_with(1, 2, 3, 4, duration=0.2, button="left")


def test_scroll(inputs, windows, context):
    action = registry.create_action("scroll", params={"amount": -5})
    action.execute(inputs, windows, context)
    inputs.scroll.assert_called_once_with(-5)


def test_key_press(inputs, windows, context):
    action = registry.create_action("key_press", params={"key": "Enter", "presses": 2, "interval": 0.1})
    action.execute(inputs, windows, context)
    inputs.press.assert_called_once_with("enter", presses=2, interval=0.1)


def test_key_press_vide_invalide():
    action = registry.create_action("key_press", params={"key": "  "})
    with pytest.raises(ValueError):
        action.validate()


def test_hotkey(inputs, windows, context):
    action = registry.create_action("hotkey", params={"keys": ["Ctrl", "End"]})
    action.execute(inputs, windows, context)
    inputs.hotkey.assert_called_once_with(["ctrl", "end"])


def test_hotkey_depuis_chaine(inputs, windows, context):
    action = registry.create_action("hotkey", params={"keys": "ctrl+c"})
    action.execute(inputs, windows, context)
    inputs.hotkey.assert_called_once_with(["ctrl", "c"])


def test_type_text(inputs, windows, context):
    action = registry.create_action("type_text", params={"text": "bonjour", "interval": 0.05})
    action.execute(inputs, windows, context)
    inputs.type_text.assert_called_once_with("bonjour", interval=0.05)


def test_wait_utilise_sleep_du_contexte(inputs, windows):
    appels = []
    context = {"sleep": appels.append}
    action = registry.create_action("wait", params={"seconds": 2.5})
    action.execute(inputs, windows, context)
    assert appels == [2.5]


def test_activate_window(inputs, windows, context):
    action = registry.create_action(
        "activate_window",
        params={"title": "Bloc-notes", "match": "contains", "force_foreground": True},
    )
    result = action.execute(inputs, windows, context)
    windows.activate.assert_called_once_with(title="Bloc-notes", match="contains", force_foreground=True)
    assert result is True


def test_activate_window_introuvable_logue(inputs, windows):
    windows.activate.return_value = False
    messages = []
    context = {"log": lambda msg, level="info": messages.append((msg, level))}
    action = registry.create_action("activate_window", params={"title": "Inexistante"})
    result = action.execute(inputs, windows, context)
    assert result is False
    assert any(level == "warning" for _msg, level in messages)


def test_activate_window_titre_vide():
    action = registry.create_action("activate_window", params={"title": ""})
    with pytest.raises(ValueError):
        action.validate()


def test_launch_app(inputs, windows, context):
    action = registry.create_action("launch_app", params={"path": "notepad.exe", "args": "a b"})
    action.execute(inputs, windows, context)
    windows.launch.assert_called_once_with("notepad.exe", ["a", "b"])


def test_wait_for_window(inputs, windows, context):
    action = registry.create_action("wait_for_window", params={"title": "Cmder", "timeout": 5})
    action.execute(inputs, windows, context)
    assert windows.wait_for_window.called


def test_screenshot(inputs, windows, context):
    action = registry.create_action("screenshot", params={"path": "out.png"})
    action.execute(inputs, windows, context)
    inputs.screenshot.assert_called_once_with("out.png", region=None)


def test_screenshot_region(inputs, windows, context):
    action = registry.create_action(
        "screenshot",
        params={"path": "out.png", "region": True, "x": 0, "y": 0, "width": 100, "height": 50},
    )
    action.execute(inputs, windows, context)
    inputs.screenshot.assert_called_once_with("out.png", region=(0, 0, 100, 50))


def test_click_image_trouve(inputs, windows, context):
    inputs.locate_center.return_value = (40, 60)
    action = registry.create_action("click_image", params={"path": "img.png"})
    action.execute(inputs, windows, context)
    inputs.click.assert_called_once_with(x=40, y=60, button="left")


def test_click_image_introuvable(inputs, windows, context):
    inputs.locate_center.return_value = None
    action = registry.create_action("click_image", params={"path": "img.png"})
    result = action.execute(inputs, windows, context)
    assert result is None
    inputs.click.assert_not_called()


def test_wait_for_image_trouve_immediatement(inputs, windows):
    inputs.locate_center.return_value = (7, 8)
    context = {"sleep": lambda _s: None}
    action = registry.create_action("wait_for_image", params={"path": "img.png", "timeout": 1})
    result = action.execute(inputs, windows, context)
    assert result == (7, 8)


def test_defaults_sont_independants():
    """Les valeurs par défaut mutables ne sont pas partagées entre instances."""
    a = registry.create_action("hotkey")
    b = registry.create_action("hotkey")
    a.params["keys"].append("zzz")
    assert "zzz" not in b.params["keys"]
