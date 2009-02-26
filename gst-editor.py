#!/usr/bin/env python
import gobject
gobject.threads_init()
import pygtk
pygtk.require("2.0")
import gtk
import os.path
import gst
from utils import hpane, vpane, scrolled, viewport, vbox
from bin import BinView
from property_editor import PropertyEditor
from browser import Browser
from gettext import gettext as _

ui = """
<ui>
    <menubar name="MainMenuBar">
        <menu action="File">
            <menuitem action="New" />
            <menuitem action="Open" />
            <menuitem action="Save" />
            <separator />
            <menuitem action="Quit" />
        </menu>
        <menu action="Edit">
            <menuitem action="Undo" />
            <menuitem action="Redo" />
            <menuitem action="Cut" />
            <menuitem action="Copy" />
            <menuitem action="Paste" />
            <separator />
            <menuitem action="Preferences" />
        </menu>
        <menu action="View" >
            <menuitem action="ZoomIn" />
            <menuitem action="ZoomOut" />
        </menu>
        <menu action="Help">
            <menuitem action="About" />
        </menu>
    </menubar>
    <toolbar name="MainToolBar">
        <toolitem action="Null" />
        <toolitem action="Ready" />
        <toolitem action="Pause" />
        <toolitem action="Play" />
    </toolbar>
</ui>
"""

class GSTEditor(gtk.Window):

    def __init__(self, m):
        gtk.Window.__init__(self)
        self.pipeline = gst.Pipeline()
        self.__createUi(m)

    def __createUi(self, m):
        self.__setupActions(m)
        self.add(
            vbox(
                (
                    m.get_widget("/MainMenuBar"),
                    "start",
                    False,
                    False,
                ),
                (
                    hpane(
                        vpane(
                            scrolled(
                                viewport(
                                    PropertyEditor()
                                )
                            ),
                            Browser(),
                        ),
                        scrolled(
                            BinView(self.pipeline, m)
                        )
                    ), 
                    "end",
                    True, 
                    True,
                ),
                (
                    m.get_widget("/MainToolBar"),
                    "start",
                    False,
                    False,
                ),
            )
        )
        self.set_default_size(640, 480)
        self.show_all()
        self.connect("destroy", self.quit)

    def __setupActions(self, m):
        actiongroup = gtk.ActionGroup("mainwindow")
        actiongroup.add_actions((
            ("New", gtk.STOCK_NEW, None, None, None, self.newPipeline),
            ("Open", gtk.STOCK_OPEN, None, None, None, self.openPipeline),
            ("Save", gtk.STOCK_SAVE, None, None, None, self.savePipeline),
            ("Quit", gtk.STOCK_QUIT, None, None, None, self.quit),
            ("Undo", gtk.STOCK_UNDO, None, None, None, self.undo),
            ("Redo", gtk.STOCK_REDO, None, None, None, self.redo),
            ("Cut", gtk.STOCK_CUT, None, None, None, self.cut),
            ("Copy", gtk.STOCK_COPY, None, None, None, self.copy),
            ("Paste", gtk.STOCK_PASTE, None, None, None, self.paste),
            ("Preferences", gtk.STOCK_PREFERENCES, None, None, None,
                self.prefs),
            ("ZoomIn", gtk.STOCK_ZOOM_IN, None, None, None, self.zoomIn),
            ("ZoomOut", gtk.STOCK_ZOOM_OUT, None, None, None, self.zoomOut),
            ("About", gtk.STOCK_ABOUT, None, None, None, self.about),
            ("File", None, _("_File")),
            ("Edit", None, _("_Edit")),
            ("Help", None, _("_Help")),
            ("View", None, _("_View")),
        ))
        actiongroup.add_toggle_actions((
            ("Null", gtk.STOCK_MEDIA_STOP, _("Null"), None, None, self.nullState),
            ("Ready", gtk.STOCK_YES, _("Ready"), None, None, self.readyState),
            ("Pause", gtk.STOCK_MEDIA_PAUSE, None, None, None, self.pausedState),
            ("Play", gtk.STOCK_MEDIA_PLAY, None, None, None,
                self.playingState),
        ))
        m.insert_action_group(actiongroup)
        m.add_ui_from_string(ui)

    def newPipeline(self, action):
        pass

    def openPipeline(self, action):
        pass

    def savePipeline(self, action):
        pass

    def quit(self, action):
        gtk.main_quit()

    def undo(self, action):
        pass

    def redo(self, action):
        pass

    def cut(self, action):
        pass

    def copy(self, action):
        pass

    def paste(self, action):
        pass

    def prefs(self, action):
        pass

    def zoomIn(self, action):
        pass

    def zoomOut(self, action):
        pass

    def about(self, action):
        pass

    def nullState(self, action):
        pass

    def readyState(self, action):
        pass

    def pausedState(self, action):
        pass

    def playingState(self, action):
        pass

if __name__ == "__main__":
    m = gtk.UIManager()
    w = GSTEditor(m)
    gtk.main()
