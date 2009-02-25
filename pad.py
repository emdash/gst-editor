from receiver import receiver, handler
import gst
import goocanvas
import controller
import view
import gtk

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

def make_pad_view(pad):
    if type(pad) == gst.Pad:
        return PadView(pad)
    elif pad.presence == gst.PAD_REQUEST:
        return RequestTemplateView(pad)
    elif pad.presence == gst.PAD_SOMETIMES:
        return SometimesTemplateView(pad)
    return None

