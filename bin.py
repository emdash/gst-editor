import os
import gst
import gtk
import goocanvas
from receiver import receiver, handler
from element import ElementView

ui = """
<ui>
    <toolbar name="MainToolBar">
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
        self.selected = set()
        self.drag_dest_set(gtk.DEST_DEFAULT_ALL, target,
            gtk.gdk.ACTION_COPY)
        self.connect("drag_data_received", self.__dragDataReceived)

    def __dragDataReceived(self, w, context, x, y, selection, targetType, time):
        if targetType == TYPE_GST_ELEMENT:
            element = gst.element_factory_make(selection.data)
        elif targetType == TYPE_TEXT_PLAIN:
            incoming = selection.data.strip()
            if isfile(incoming):
                element = gst.element_factory_make("filesrc",
                    os.path.basename(incoming))
                element.props.location = incoming
        self.addElement(element, *self.convert_from_pixels(x, y))

    def addElement(self, element, x, y):
        element.set_data("pos", (x, y))
        self.pipeline.add(element)

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

