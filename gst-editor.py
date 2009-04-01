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
from pad import PadView
from property_editor import PropertyEditor
from element import ElementView
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
        <placeholder name="BinMenus" />
        <menu action="View" >
            <menuitem action="ZoomIn" />
            <menuitem action="ZoomOut" />
        </menu>
        <menu action="Help">
            <menuitem action="About" />
        </menu>
    </menubar>
    <toolbar name="MainToolBar">
        <placeholder name="BinActions" />
        <separator />
        <toolitem action="Null" />
        <toolitem action="Ready" />
        <toolitem action="Pause" />
        <toolitem action="Play" />
    </toolbar>
</ui>
"""

class PretendToggleButton(gtk.Button):

    def __init__(self):
        gtk.Button.__init__(self)
        self.set_relief(gtk.RELIEF_NONE)

    def setActive(self, state):
        if state:
            self.set_relief(gtk.RELIEF_HALF)
        else:
            self.set_relief(gtk.RELIEF_NONE)

class PipelineStateAction(gtk.Action):

    __gtype_name__ = "PipelineStateAction"
    __gsignals__ = {
        "activate" : "override",
    }

    state_actions = {
        gst.STATE_NULL : ("Null", _("Null"), None, gtk.STOCK_MEDIA_STOP),
        gst.STATE_READY : ("Ready",  _("Ready"), None, gtk.STOCK_YES),
        gst.STATE_PAUSED : ("Pause", _("Pause"), None, gtk.STOCK_MEDIA_PAUSE), 
        gst.STATE_PLAYING : ("Play", _("Play"), None, gtk.STOCK_MEDIA_PLAY),
    }

    def __init__(self, state, pipeline, *args, **kwargs):
        gtk.Action.__init__(self, *args, **kwargs)
        self.state = state
        self.pipeline = pipeline
        bus = pipeline.get_bus()
        bus.connect("message", self.__messageHandler)

    def __messageHandler(self, bus, message):
        if message.type == gst.MESSAGE_STATE_CHANGED:
            old, new, pending = message.parse_state_changed()
            if old == self.state:
                self.deactivateProxies()
            if pending == self.state:
                self.deactivateProxies()
            if new == self.state:
                self.activateProxies()

    def do_create_tool_item(self):
        ret = gtk.ToolItem()
        ret.set_border_width(2)
        button = PretendToggleButton()
        button.add(
            vbox(
                (
                    self.create_icon(
                        gtk.ICON_SIZE_SMALL_TOOLBAR),
                    False,
                    False,
                    "Start",
                ),
                (
                    gtk.Label(self.props.label),
                    False,
                    False,
                    "End",
                )
            )
        )
        button.connect("clicked", self.clicked)
        ret.add(button)
        ret.show_all()
        ret.set_homogeneous(True)
        # warning: hack alert!
        ret.setActive = button.setActive
        return ret

    def clicked(self, button):
        if self.state == gst.STATE_NULL:
            PadView.unblock_all_pads()
            ElementView.set_all_to_null()
        self.pipeline.set_state(self.state)

    def deactivateProxies(self):
        for proxy in self.get_proxies():
            proxy.setActive(False)

    def activateProxies(self):
        for proxy in self.get_proxies():
            proxy.setActive(True)

    @classmethod
    def addStateActions(cls, actiongroup, pipeline):
        for state, info in cls.state_actions.iteritems():
            action = PipelineStateAction(state, pipeline, *info)
            actiongroup.add_action(action)

class GSTEditor(gtk.Window):

    def __init__(self, m):
        gtk.Window.__init__(self)
        self.pipeline = gst.Pipeline()
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
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
        PipelineStateAction.addStateActions(actiongroup, self.pipeline)
        m.insert_action_group(actiongroup, 0)
        m.add_ui_from_string(ui)

    def __messageHandler(self, bus, message):
        if message.type == gst.MESSAGE_STATE_CHANGED:
            old, new, pending = message.parse_state_changed()
            old_action = self.actiongroup.get_action(actions[old])
            new_action = self.actiongroup.get_action(actions[new])

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

if __name__ == "__main__":
    m = gtk.UIManager()
    w = GSTEditor(m)
    gtk.main()
