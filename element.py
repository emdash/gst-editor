import goocanvas
import controller
import view
import gtk
import gst
from pad import make_pad_view
from receiver import receiver, handler

class ElementView(view.View, goocanvas.Group):

    __NORMAL__ = 0x709fb899
    __SELECTED__ = 0xa6cee3AA

    class Controller(controller.Controller):

        def click(self, pos):
            self._view.select()

    def __init__(self, element):
        goocanvas.Group.__init__(self)
        view.View.__init__(self)
        self.element = element
        self.bg = goocanvas.Rect(
            parent = self,
            fill_color = "grey",
            radius_x = 5,
            radius_y = 5)

        self.text = goocanvas.Text(
            parent = self,
            x = 0,
            y = 0,
            width = -1,
            font = "Sans 9",
            text = element.get_name())

        self.__pads = {}

        for pad in element.get_pad_template_list():
            self.__show_pad(pad)

        for pad in element.pads():
            self.__show_pad(pad)

## view methods

    def select(self):
        self.props.stroke_color = "red"

    def normal(self):
        self.props.stroke_color = "black"

    element = receiver()

## element signal handlers

    @handler(element, "pad-added")
    def __pad_added(self, element, pad):
        # this handler is called in pipeline context, and we need to add the
        # pad in the UI context
        print pad.get_name(), pad.get_direction(), pad
        gobject.idle_add(self.__show_pad, pad)

    @handler(element, "pad-removed")
    def __pad_removed(self, element, pad):
        print pad.get_name(), pad.get_direction(), pad
        # this handler is called in pipeline context, and we need to add the
        # pad in the UI context
        gobject.idle_add(self.__hide_pad, pad)

## implementation functions

    __cur_row = 0

    def __update(self):
        #for 
        pass

    def __show_pad(self, pad):
        child = make_pad_view(pad)
        self.__pads[pad] = child
        self.__cur_row += 1
        return False

    def __hide_pad(self, pad):
        return False


