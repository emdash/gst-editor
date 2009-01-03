import gobject
gobject.threads_init()
import goocanvas
import controller
import view
import gtk
import os.path
import pango
import gst
from receiver import receiver, handler

class PadBaseView(view.View, goocanvas.Rect):

    __COLOR__ = "yellow"
    __INACTIVE__ = "black"
    __ACTIVE__ = "red"
    __BLOCKED__ = "yellow"

    class Controller(controller.Controller):

        __ARROW_COLOR__ = "red"

        arrow = goocanvas.Polyline(
            stroke_color = __ARROW_COLOR__,
            end_arrow = "true")

        def drag_start(self):
            pass

        def drag_end(self):
            pass

    def __init__(self, pad):
        goocanvas.Rect.__init__(self,
            width = 10,
            height = 10,
            fill_color = self.__COLOR__)
        view.View.__init__(self)
        self.pad = pad

class PadView(PadBaseView, goocanvas.Group):

    def __init__(self, pad):
        PadBaseView.__init__(self, pad)
        self.block()

## pad signal handlers

    pad = receiver()
    # yes, we wan't this to be a static list
    blocked_pads = []

## implementation

    @classmethod
    def unblock_all_pads(cls):
        for pad in cls.blocked_pads:
            pad.unblock()

    def link_pads(self, target):
        pass

    def block(self):
        self.pad.set_blocked_async(True, self.__block_cb)

    def unblock(self):
        self.pad.set_blocked_async(False, self.__block_cb)

    def __finish_pad_blocking(self, blocked):
        if blocked:
            self.blocked_pads.append(self)
            self.props.fill_color = self.__BLOCKED__
        else:
            self.props.fill_color = self.__NORMAL__
            self.blocked_pads.remove(self)
        return False

    def __block_cb(self, state):
        # this callback is called from pipeline context, and we need to do UI
        # tasks in the main context
        gobject.idle_add(self.__finish_pad_blocking, state)

class RequestTemplateView(PadBaseView):

    __COLOR__ = "blue"

    class Controller(controller.Controller):

        def click(self):
            pass

class SometimesTemplateView(PadView):

    __COLOR__ = "green"

    class Controller(controller.Controller):

        def click(self):
            pass

class ElementView(view.View, goocanvas.Table):

    __NORMAL__ = 0x709fb899
    __SELECTED__ = 0xa6cee3AA

    class Controller(controller.Controller):

        def click(self, pos):
            self._view.select()

    def __init__(self, element):
        goocanvas.Table.__init__(self)
        view.View.__init__(self)
        self.element = element
        self.bg = goocanvas.Rect(
            parent = self,
            fill_color = "grey",
            radius_x = 5,
            radius_y = 5)
        self.set_child_properties(self.bg,
            row = 0,
            rows = 1,
            column = 0,
            columns = 4,
            x_expand = True,
            x_shrink = True,
            x_fill = True,
            y_expand = True,
            y_shrink = True,
            y_fill = True)
        self.text = goocanvas.Text(
            parent = self,
            x = 0,
            y = 0,
            width = -1,
            font = "Sans 9",
            text = element.get_name())
        self.set_child_properties(self.text,
            row = 0,
            rows = 1,
            column = 0,
            columns = 4,
            x_expand = True,
            x_fill = True,
            x_shrink = True,
            y_expand = False,
            y_shrink = True,
            y_fill = False)

        self.__pads = {}
        self.__cur_row = 0

        for pad in element.get_pad_template_list():
            if pad.presence == gst.PAD_REQUEST or gst.PAD_SOMETIMES:
                self.__pad_added(self.element, pad)

        for pad in element.pads():
            self.__pad_added(self.element, pad)

## view methods

    def select(self):
        self.props.stroke_color = "red"

    def normal(self):
        self.props.stroke_color = "black"

    element = receiver()

## element signal handlers

    @handler(element, "pad-added")
    def __pad_added(self, element, pad):
        print pad
        print pad.get_name(), pad.get_caps()
        # this handler is called in pipeline context, and we need to add the
        # pad in the UI context
        gobject.idle_add(self.__show_pad, pad)

    @handler(element, "pad-removed")
    def __pad_removed(self, element, pad):
        print pad.get_name(), pad.get_direction(), pad
        # this handler is called in pipeline context, and we need to add the
        # pad in the UI context
        gobject.idle_add(self.__hide_pad, pad)

## implementation functions

    def __show_pad(self, pad):
        child = PadView(pad, self.element)
        text = goocanvas.Text(
            parent = self,
            text = pad.get_name(),
            font = "Sans 8")
        if pad.get_direction() == gst.DIRECTION_SRC:
            column = 3
            tcol = 2
        else:
            column = 0
            tcol = 1
        self.set_child_properties(child,
            row = self.__cur_row,
            column = column)
        self.set_child_properties(text,
            row = self.__cur_row,
            column = tcol)
        self.__pads.append((pad, text))
        self.__cur_row += 1
        return False

    def __hide_pad(self, pad):
        return False

           

class PipelineView(goocanvas.Canvas):

    widgets = None
    selected = None

    def __init__(self, pipeline):
        goocanvas.Canvas.__init__(self)
        self.pipeline = pipeline
        self.widgets = {}
        self.selected = set()
        pipeline.add(gst.element_factory_make("fakesink"))

    pipeline = receiver()

    @handler(pipeline, "element-added")
    def element_added(self, pipeline, element):
        v = ElementView(element)
        self.widgets[element] = v
        self.get_root_item().add_child(v)

    @handler(pipeline, "element-removed")
    def element_removed(self, pipeline, element):
        if element in self.widgets:
            self.widgets[element].remove()

if __name__ == "__main__":
    w = gtk.Window()
    p = PipelineView(gst.Pipeline())
    w.add(p)
    w.connect("destroy", gtk.main_quit)
    w.show_all()
    gtk.main()
