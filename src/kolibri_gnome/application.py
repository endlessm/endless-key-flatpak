from __future__ import annotations

import json
import logging
import typing
from functools import partial
from gettext import gettext as _
from pathlib import Path
from urllib.parse import urlsplit

from gi.repository import Adw
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import WebKit
from kolibri_app.config import APP_URI_SCHEME
from kolibri_app.config import BASE_APPLICATION_ID
from kolibri_app.config import BASE_OBJECT_PATH
from kolibri_app.config import KOLIBRI_APP_DATA_DIR
from kolibri_app.config import KOLIBRI_URI_SCHEME
from kolibri_app.globals import get_release_notes_version
from kolibri_app.globals import get_version
from kolibri_app.globals import XDG_CURRENT_DESKTOP

from .kolibri_context import KolibriChannelContext
from .kolibri_context import KolibriContext
from .kolibri_webview import KolibriWebView
from .kolibri_window import KolibriWindow

logger = logging.getLogger(__name__)


class Application(Adw.Application):
    __context: KolibriContext

    application_name = GObject.Property(type=str, default=_("Endless Key"))

    def __init__(
        self, *args, context: typing.Optional[KolibriContext] = None, **kwargs
    ):
        super().__init__(*args, flags=Gio.ApplicationFlags.HANDLES_OPEN, **kwargs)

        resource = Gio.Resource.load(
            Path(KOLIBRI_APP_DATA_DIR, "kolibri-app.gresource").as_posix()
        )
        resource._register()

        self.__context = context or KolibriContext()
        self.__context.connect("download-started", self.__context_on_download_started)
        self.__context.connect("open-external-url", self.__context_on_open_external_url)

        action = Gio.SimpleAction.new("open-documentation", None)
        action.connect("activate", self.__on_open_documentation)
        self.add_action(action)

        action = Gio.SimpleAction.new("new-window", None)
        action.connect("activate", self.__on_new_window)
        self.add_action(action)

        action = Gio.SimpleAction.new("about", None)
        action.connect("activate", self.__on_about)
        self.add_action(action)

        action = Gio.SimpleAction.new("quit", None)
        action.connect("activate", self.__on_quit)
        self.add_action(action)

        self.set_accels_for_action("app.open-documentation", ["F1"])
        self.set_accels_for_action("app.new-window", ["<Control>n"])
        self.set_accels_for_action("app.quit", ["<Control>q"])

        KolibriWindow.set_accels(self)

    @property
    def context(self):
        return self.__context

    def do_startup(self):
        Adw.Application.do_startup(self)

        self.__context.init()

    def do_activate(self):
        Adw.Application.do_activate(self)

        if not self.get_windows():
            self.open_kolibri_window()

    def do_open(self, files: typing.List[Gio.File], files_count: int, hint: str):
        for file in files:
            self.__handle_open_file_url(file.get_uri())

    def do_shutdown(self):
        Adw.Application.do_shutdown(self)

        self.__context.shutdown()

    def __on_open_documentation(self, action, *args):
        self.open_url_in_external_application(
            "https://support.endlessos.org/en/endless-key"
        )

    def __on_new_window(self, action, *args):
        self.open_kolibri_window()

    def __on_about(self, action, *args):
        about_window = Adw.AboutWindow.new_from_appdata(
            f"{BASE_OBJECT_PATH}/{BASE_APPLICATION_ID}.metainfo.xml",
            get_release_notes_version(),
        )
        about_window.set_version(get_version())
        about_window.add_link(
            _("Community Forums"), "https://community.endlessos.com/c/endless-key"
        )
        about_window.set_debug_info(self.__format_debug_info())
        about_window.set_debug_info_filename("endless-key-debug-info.json")
        about_window.set_transient_for(self.get_active_window())
        about_window.set_modal(True)
        about_window.present()

    def __format_debug_info(self):
        return json.dumps(
            self.__context.get_debug_info(),
            indent=4,
        )

    def __on_quit(self, action, *args):
        self.quit()

    def open_url_in_external_application(self, url: str):
        url_file = Gio.File.new_for_uri(url)
        file_launcher = Gtk.FileLauncher.new(url_file)
        file_launcher.launch(None, None, None)

    def open_kolibri_window(
        self, target_url: typing.Optional[str] = None, **kwargs
    ) -> typing.Optional[KolibriWindow]:
        target_url = target_url or self.__context.default_url

        if not self.__context.should_open_url(target_url):
            self.open_url_in_external_application(target_url)
            return None

        window = KolibriWindow(application=self, context=self.__context, **kwargs)

        window.connect("open-new-window", self.__window_on_open_new_window)
        window.load_kolibri_url(target_url, present=True)

        # Maximize windows on Endless OS. Typically $XDG_CURRENT_DESKTOP will be
        # `endless:GNOME` or `Endless:GNOME`.
        if XDG_CURRENT_DESKTOP and "endless" in XDG_CURRENT_DESKTOP.lower().split(":"):
            window.maximize()

        window.connect("auto-close", self.__kolibri_window_on_auto_close)

        # In some cases, a window will be created with a URL that returns an
        # unsupported content type. In this case, WebKit will start a download
        # and the window will be immediately auto-closed. To avoid showing a
        # window for a split second, we will wait for 500 ms, which is usually
        # enough time to determine if the target URL will trigger a download.

        GLib.timeout_add(
            500, partial(self.__kolibri_window_auto_show_timeout_cb, window)
        )

        return window

    def __kolibri_window_auto_show_timeout_cb(self, window: KolibriWindow) -> bool:
        if window.get_application() == self:
            window.show()
        return GLib.SOURCE_REMOVE

    def __kolibri_window_on_auto_close(self, window: KolibriWindow):
        window.close()
        self.remove_window(window)

    def __context_on_download_started(
        self, context: KolibriContext, download: WebKit.Download
    ):
        download.connect("decide-destination", self.__download_on_decide_destination)
        download.connect("finished", self.__download_on_finished)

    def __download_on_decide_destination(
        self, download: WebKit.Download, suggested_filename: str
    ) -> bool:
        file_chooser = Gtk.FileChooserNative.new(
            _("Save File"),
            self.get_active_window(),
            Gtk.FileChooserAction.SAVE,
            None,
            None,
        )
        file_chooser.set_current_name(suggested_filename)

        # We need to create a nested loop to wait for the response signal,
        # because WebKit's download API doesn't allow setting a destination
        # asynchronously: <https://bugs.webkit.org/show_bug.cgi?id=238748>

        nested_loop = GLib.MainLoop.new(None, False)
        file_chooser.connect(
            "response", partial(self.__download_file_chooser_on_response, download)
        )
        file_chooser.connect("response", lambda *args: nested_loop.quit())
        file_chooser.show()
        nested_loop.run()

        if not download.get_destination():
            return False

        return True

    def __download_file_chooser_on_response(
        self,
        download: WebKit.Download,
        file_chooser: Gtk.FileChooserNative,
        response: Gtk.ResponseType,
    ):
        if response != Gtk.ResponseType.ACCEPT:
            download.cancel()
            return
        response_file = file_chooser.get_file()
        download.set_allow_overwrite(True)
        download.set_destination(response_file.get_path())

    def __download_on_finished(self, download: WebKit.Download):
        download_destination = download.get_destination()

        if not download_destination:
            return

        download_file = Gio.File.new_for_path(download_destination)

        file_launcher = Gtk.FileLauncher.new(download_file)
        file_launcher.open_containing_folder(None, None, None)

    def __context_on_open_external_url(
        self, context: KolibriContext, external_url: str
    ):
        self.open_url_in_external_application(external_url)

    def __window_on_open_new_window(
        self, window: KolibriWindow, target_url: str, related_webview: WebKit.WebView
    ) -> typing.Optional[KolibriWebView]:
        new_window = self.open_kolibri_window(
            target_url, related_webview=related_webview
        )
        return new_window.get_main_webview() if new_window else None

    def __handle_open_file_url(self, url: str):
        valid_url_schemes = (KOLIBRI_URI_SCHEME, APP_URI_SCHEME)

        url_tuple = urlsplit(url)

        if url_tuple.scheme not in valid_url_schemes:
            logger.info("Invalid URL scheme: %s", url)
            return

        active_window = self.get_active_window()

        if isinstance(active_window, KolibriWindow):
            active_window.load_kolibri_url(url, present=True)
        else:
            self.open_kolibri_window(url)


class ChannelApplication(Application):
    __channel_id: str

    def __init__(self, channel_id: str, *args, **kwargs):
        self.__channel_id = channel_id

        context = KolibriChannelContext(channel_id)
        context.connect("kolibri-ready", self.__context_on_kolibri_ready)

        super().__init__(*args, context=context, **kwargs)

    def __context_on_kolibri_ready(self, context: KolibriContext):
        context.kolibri_api_get_async(
            "/api/content/channel/{channel_id}".format(channel_id=self.__channel_id),
            result_cb=self.__on_kolibri_api_channel_response,
        )

    def __on_kolibri_api_channel_response(self, data: typing.Any):
        if not isinstance(data, dict):
            return

        channel_name = data.get("name")

        if channel_name:
            self.props.application_name = channel_name
