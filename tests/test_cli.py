"""Unit tests voor flex2rijk CLI."""

from pathlib import Path
from typing import Any

import pytest
from flex2rijk.cli import keychain_get, keychain_set, open_ica


def test_keychain_get_success(mocker: Any) -> None:
    """Test succesvol ophalen van wachtwoord."""
    if Path("/usr/bin/security").exists() or Path("/usr/local/bin/security").exists():
        # Mock macOS subprocess run
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "secret_password\n"
        mocker.patch("platform.system", return_value="Darwin")

        result = keychain_get("username")
        assert result == "secret_password"
    else:
        # Mock keyring for other platforms
        mock_keyring = mocker.patch("flex2rijk.cli.keyring")
        mock_keyring.get_password.return_value = "secret_password"
        mocker.patch("platform.system", return_value="Linux")

        result = keychain_get("username")
        assert result == "secret_password"


def test_keychain_get_failure(mocker: Any) -> None:
    """Test falen van ophalen."""
    mocker.patch("platform.system", return_value="Darwin")
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 1

    with pytest.raises(SystemExit):
        keychain_get("username")


def test_keychain_set_success(mocker: Any) -> None:
    """Test succesvol opslaan."""
    mocker.patch("platform.system", return_value="Darwin")
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 0

    keychain_set("username", "new_password")

    # Check that it tried to add the password
    assert mock_run.call_count >= 1


def test_open_ica_macos(mocker: Any) -> None:
    """Test openen van ICA op macOS."""
    mocker.patch("platform.system", return_value="Darwin")
    mock_popen = mocker.patch("subprocess.Popen")
    mocker.patch.object(Path, "exists", return_value=True)

    path = Path("/tmp/test.ica")
    open_ica(path)

    mock_popen.assert_called_once_with(["open", str(path.absolute())])


def test_open_ica_windows(mocker: Any) -> None:
    """Test openen van ICA op Windows."""
    mocker.patch("platform.system", return_value="Windows")
    mock_startfile = mocker.patch("os.startfile", create=True)
    mocker.patch.object(Path, "exists", return_value=True)

    path = Path("C:/temp/test.ica")
    open_ica(path)

    mock_startfile.assert_called_once_with(str(path.absolute()))


def test_open_ica_linux(mocker: Any) -> None:
    """Test openen van ICA op Linux."""
    mocker.patch("platform.system", return_value="Linux")
    mock_popen = mocker.patch("subprocess.Popen")
    mocker.patch.object(Path, "exists", return_value=True)

    path = Path("/tmp/test.ica")
    open_ica(path)

    mock_popen.assert_called_once_with(["xdg-open", str(path.absolute())])
