"""Unit tests voor flex2rijk CLI."""

from pathlib import Path
from typing import Any

import pytest
from flex2rijk.cli import keychain_get, keychain_set, open_ica


def test_keychain_get_success(mocker: Any) -> None:
    """Test succesvol ophalen van wachtwoord uit keychain."""
    # Mock keyring
    mock_keyring = mocker.patch("flex2rijk.cli.keyring")
    mock_keyring.get_password.return_value = "secret_password"

    result = keychain_get("username")

    assert result == "secret_password"
    mock_keyring.get_password.assert_called_once_with("flex2rijk", "username")


def test_keychain_get_failure(mocker: Any) -> None:
    """Test falen van ophalen uit keychain."""
    # Mock keyring to return None
    mock_keyring = mocker.patch("flex2rijk.cli.keyring")
    mock_keyring.get_password.return_value = None

    with pytest.raises(SystemExit):
        keychain_get("username")


def test_keychain_set_success(mocker: Any) -> None:
    """Test succesvol opslaan in keychain."""
    # Mock keyring
    mock_keyring = mocker.patch("flex2rijk.cli.keyring")

    keychain_set("username", "new_password")

    mock_keyring.set_password.assert_called_once_with("flex2rijk", "username", "new_password")


def test_open_ica_macos(mocker: Any) -> None:
    """Test openen van ICA op macOS."""
    # Mock platform and subprocess
    mocker.patch("platform.system", return_value="Darwin")
    mock_popen = mocker.patch("subprocess.Popen")

    path = Path("/tmp/test.ica")
    open_ica(path)

    mock_popen.assert_called_once_with(["open", str(path)])


def test_open_ica_windows(mocker: Any) -> None:
    """Test openen van ICA op Windows."""
    # Mock platform and os
    mocker.patch("platform.system", return_value="Windows")
    mock_startfile = mocker.patch("os.startfile", create=True)
    mocker.patch("os.path.exists", return_value=True)

    path = Path("C:/temp/test.ica")
    open_ica(path)

    mock_startfile.assert_called_once_with(str(path))


def test_open_ica_linux(mocker: Any) -> None:
    """Test openen van ICA op Linux."""
    # Mock platform and subprocess
    mocker.patch("platform.system", return_value="Linux")
    mock_popen = mocker.patch("subprocess.Popen")

    path = Path("/tmp/test.ica")
    open_ica(path)

    mock_popen.assert_called_once_with(["xdg-open", str(path)])
