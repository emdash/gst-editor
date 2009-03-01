import os
import gst
import gtk
from gettext import gettext as _
import goocanvas
from receiver import receiver, handler
from element import ElementView

ui = """
<ui>
    <menubar name="MainMenuBar">
        <placeholder name="BinMenus">
            <menu action="Bin">
                <menuitem action="AddFile" />
            </menu>
        </placeholder>
    </menubar>
    <toolbar name="MainToolBar">
        <placeholder name="BinActions">
            <toolitem action="AddFile" />
            <toolitem action="Delete" />
        </placeholder>
    </toolbar>
</ui>
"""

TYPE_GST_ELEMENT = 0
TYPE_TEXT_PLAIN = 24

target = [
    ('GST_ELEMENT', 0, TYPE_GST_ELEMENT),
    ('text/plain', 0, TYPE_TEXT_PLAIN),
]

def isfile(path):
    if path[:7] == "file://":
        # either it's on local system and we know if it's a directory
        return os.path.isfile(path[7:])
    elif "://" in path:
        # or it's not, in which case we assume it's a file
        return True
    # or it's on local system with "file://"
    return os.path.isfile(path)

class BinView(goocanvas.Canvas):

    widgets = None
    selected = None

    def __init__(self, pipeline, m):
        goocanvas.Canvas.__init__(self)
        self.props.automatic_bounds = True
        self.pipeline = pipeline
        self.widgets = {}
        self.drag_dest_set(gtk.DEST_DEFAULT_ALL, target,
            gtk.gdk.ACTION_COPY)
        self.connect("drag_data_received", self.__dragDataReceived)
        self.selected = set()
        self.__setupActions(m)

    def __setupActions(self, m):
        actiongroup = gtk.ActionGroup("binview")
        actiongroup.add_actions((
            ("AddFile", gtk.STOCK_ADD, _("Add Filesrc"), None, None,
                self.addFileAction),
            ("Delete", gtk.STOCK_DELETE, None, None, None,
                self.deleteSelectionAction),
            ("Bin", None, _("_Bin")),
        ))
        m.insert_action_group(actiongroup)
        m.add_ui_from_string(ui)

    def __dragDataReceived(self, w, context, x, y, selection, targetType, time):
        if targetType == TYPE_GST_ELEMENT:
            elements = selection.data.split('\n')
            for factory in elements:
                element = gst.element_factory_make(factory)
                self.addElement(element, x, y)
                x += 10; y += 10
        elif targetType == TYPE_TEXT_PLAIN:
            incoming = [uri.strip() for uri in selection.data.split('\n')]
            for uri in incoming:
                if isfile(uri):
                    self.addFile(uri, *self.convert_from_pixels(x, y))
                    x += 10; y += 10

    def addFileAction(self, action):
        pass

    def addFile(self, uri, x=100, y=100):
        element = gst.element_factory_make("filesrc", 
            os.path.basename(uri))
        element.props.location = uri 
        self.addElement(element, x, y)

    def addElement(self, element, x, y):
        element.set_data("pos", (x, y))
        self.pipeline.add(element)

    def deleteSelectionAction(self):
        pass

    pipeline = receiver()

    @handler(pipeline, "element-added")
    def element_added(self, pipeline, element):
        v = ElementView(element)
        self.widgets[element] = v
        x, y = element.get_data("pos")
        v.set_simple_transform(x, y, 1.0, 0)
        self.get_root_item().add_child(v)

    @handler(pipeline, "element-removed")
    def element_removed(self, pipeline, element):
        if element in self.widgets:
            self.widgets[element].remove()
