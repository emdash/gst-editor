import gobject
import goocanvas
import controller
import view
import selectable
import gtk
import gst
import utils
import weakref
from pad import make_pad_view
from receiver import receiver, handler

class ElementView(selectable.Selectable, goocanvas.Group):

    __NORMAL__ = 0x709fb899
    __SELECTED__ = 0xa6cee3AA

    padding = 2

    def __init__(self, element, selection):
        goocanvas.Group.__init__(self)
        selectable.Selectable.__init__(self, selection)
        self.register_instance(self)
        self.element = element
        self.bg = goocanvas.Rect(
            parent = self,
            fill_color = "grey",
            radius_x = 5,
            radius_y = 5)

        self.text = goocanvas.Text(
            parent = self,
            font = "Sans 8 Bold",
            text = element.get_name())

        self.__sourcePads = {}
        self.__sinkPads = {}
        self.__links = {}

        for pad in element.get_pad_template_list():
            if pad.presence != gst.PAD_ALWAYS:
                self.__addPad(pad)

        for pad in element.pads():
            self.__addPad(pad)

## public api

    def joinLink(self, pad, linkObj):
        self.__links[pad] = pad.direction()
    
    def breakLink(self, pad):
        del self.__links[pad]

    def set_simple_transform(self, x, y, scale, rotation):
        goocanvas.Group.set_simple_transform(self, x, y, scale, rotation)
        for pad in self.__sourcePads.values():
            pad.updateLinks()
        for pad in self.__sinkPads.values():
            pad.updateLinks()

## Selectable Methods methods

    def select(self):
        self.bg.props.stroke_color = "red"

    def deselect(self):
        self.bg.props.stroke_color = "black"

    def delete(self):
        p = self.element.get_parent()
        if p:
            p.remove(self.element)

    element = receiver()

## element signal handlers

    @handler(element, "pad-added")
    def __padAdded(self, element, pad):
        # this handler is called in pipeline context, and we need to add the
        # pad in the UI context
        print pad.get_name(), pad.get_direction(), pad
        gobject.idle_add(self.__addPad, pad)

    @handler(element, "pad-removed")
    def __padRemoved(self, element, pad):
        print pad.get_name(), pad.get_direction(), pad
        # this handler is called in pipeline context, and we need to add the
        # pad in the UI context
        gobject.idle_add(self.__removePad, pad)

## implementation functions

    def __sizepads(self, pads):
        width = 0
        height = 0
        for pad, widget in pads.iteritems():
            height += widget.height
            width = max(width, widget.width)
        return width, height

    def __pospads(self, pads, x, y):
        for widget in pads.itervalues():
            widget.set_simple_transform(x, y, 1.0, 0)
            y += widget.height

    def __update(self):
        twidth, theight = utils.get_text_dimensions(self.text)
        lwidth, lheight = self.__sizepads(self.__sinkPads)
        rwidth, rheight = self.__sizepads(self.__sourcePads)
        width = max(twidth, lwidth + rwidth)
        height = theight + max(lheight, rheight) + 5
        self.bg.props.width = width
        self.bg.props.height = height
        self.__pospads(self.__sinkPads, 0, theight)
        self.__pospads(self.__sourcePads, width - rwidth, theight)

    def __addPad(self, pad):
        child = make_pad_view(pad, self, self.selection)
        if child.direction() == gst.PAD_SRC:
            self.__sourcePads[pad] = child
        else:
            self.__sinkPads[pad] = child
        self.add_child(child)
        self.__update()

    def __removePad(self, pad):
        if pad.get_direction() == gst.PAD_SRC:
            widget = self.__sourcePads[pad]
            del self.__sourcePads[pad]
        else:
            widget = self.__sinkPads[pad]
            del self.__sinkPads[pad]
        widget.unlinkAll()
        widget.remove()
        self.__update()

## class methods

    __instances__ = []

    @classmethod
    def register_instance(cls, instance):
        cls.__instances__.append(weakref.proxy(instance,
            cls.unregister_instance))

    @classmethod
    def unregister_instance(cls, proxy):
        self.__instances__.remove(proxy)

    @classmethod
    def set_all_to_null(cls):
        for instance in cls.__instances__:
            instance.element.set_state(gst.STATE_NULL)
