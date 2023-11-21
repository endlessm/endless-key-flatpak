from __future__ import annotations

import gettext
import logging
import os
import typing
from pathlib import Path

from . import config
from .utils import getenv_as_bool

logger = logging.getLogger(__name__)

APP_DEVELOPER_EXTRAS = getenv_as_bool(
    config.PROFILE_ENV_PREFIX + "APP_DEVELOPER_EXTRAS",
    default=config.BUILD_PROFILE == "development",
)

APP_AUTOMATIC_LOGIN = getenv_as_bool(
    config.PROFILE_ENV_PREFIX + "APP_AUTOMATIC_LOGIN", default=True
)

APP_AUTOMATIC_PROVISION = getenv_as_bool(
    config.PROFILE_ENV_PREFIX + "APP_AUTOMATIC_PROVISION", default=True
)

XDG_CURRENT_DESKTOP = os.environ.get("XDG_CURRENT_DESKTOP")

# Logic for KOLIBRI_HOME that mimics kolibri.utils.conf except that
# $XDG_DATA_HOME/kolibri is used rather than ~/.kolibri so that the home
# directory doesn't need to be exposed in the flatpak.
if "XDG_DATA_HOME" in os.environ:
    XDG_DATA_HOME = Path(os.environ["XDG_DATA_HOME"]).expanduser().absolute()
else:
    XDG_DATA_HOME = Path.home().joinpath(".local/share")
DEFAULT_KOLIBRI_HOME_PATH = XDG_DATA_HOME.joinpath("kolibri")
if "KOLIBRI_HOME" in os.environ:
    KOLIBRI_HOME_PATH = Path(os.environ["KOLIBRI_HOME"]).expanduser().absolute()
else:
    KOLIBRI_HOME_PATH = DEFAULT_KOLIBRI_HOME_PATH

    # Set KOLIBRI_HOME now so that kolibri's initialization doesn't set
    # it back to ~/.kolibri.
    os.environ["KOLIBRI_HOME"] = KOLIBRI_HOME_PATH.as_posix()


def init_gettext():
    gettext.bindtextdomain(config.GETTEXT_PACKAGE, config.LOCALE_DIR)
    gettext.textdomain(config.GETTEXT_PACKAGE)


def init_logging(log_file_name: str = "kolibri-app.txt", level: int = logging.DEBUG):
    from kolibri.utils.logger import KolibriTimedRotatingFileHandler

    logging.basicConfig(level=level)

    try:
        logs_dir_path = KOLIBRI_HOME_PATH.joinpath("logs")
        logs_dir_path.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        # This is handled in the following block
        pass

    if not os.access(logs_dir_path, os.W_OK):
        logs_dir_path = DEFAULT_KOLIBRI_HOME_PATH.joinpath("logs")
        logs_dir_path.mkdir(parents=True, exist_ok=True)

    log_file_path = logs_dir_path.joinpath(log_file_name)

    root_logger = logging.getLogger()
    file_handler = KolibriTimedRotatingFileHandler(
        filename=log_file_path.as_posix(), when="midnight", backupCount=30
    )

    root_logger.addHandler(file_handler)

    return logs_dir_path


def get_version() -> str:
    if config.BUILD_PROFILE == "development":
        return config.VCS_TAG
    else:
        return config.PROJECT_VERSION


def get_release_notes_version() -> str:
    if config.BUILD_PROFILE == "development":
        return config.PROJECT_VERSION + "+next"
    else:
        return config.PROJECT_VERSION


def get_current_language() -> typing.Optional[str]:
    try:
        translations = gettext.translation(
            config.GETTEXT_PACKAGE, localedir=config.LOCALE_DIR
        )
        locale_info = translations.info()
    except FileNotFoundError as e:
        logger.warning("Error loading translation file: %s", e)
        language = None
    else:
        language = locale_info.get("language")

    return language
