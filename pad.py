from receiver import receiver, handler
import gst
import goocanvas
import controller
import view
import gtk
import utils
from point import Point

class PadBaseView(view.View, goocanvas.Group):

    spacing = 3

    class Controller(controller.Controller):

        __ARROW_COLOR__ = "red"

        arrow = goocanvas.Polyline(
            stroke_color = __ARROW_COLOR__)

        __center = None

        def drag_start(self):
            self._canvas.get_root_item().add_child(self.arrow)
            self.__center = self.center(self._view.socket)
            points = [self.__center, self.__center]
            self.arrow.props.points = goocanvas.Points(points)

        def drag_end(self):
            self.arrow.remove()

        def set_pos(self, obj, pos):
            points = [self.__center, pos]
            self.arrow.props.points = goocanvas.Points(points)

    def __init__(self, pad):
        self.pad = pad
        goocanvas.Group.__init__(self)
        view.View.__init__(self)
        self.__createUi()

    def __createUi(self):
        self.text = goocanvas.Text(
            font = "Sans 8",
            parent = self,
            text = self.name())

        self.socket = goocanvas.Rect(
            parent = self,
            width = 10,
            height = 10,
            fill_color = self.__COLOR__)

        twidth, theight = utils.get_text_dimensions(self.text)
        self.width = self.spacing + self.socket.props.width + twidth
        self.height = max(self.socket.props.height, theight)

        if self.direction() == gst.PAD_SRC:
            self.socket.props.x = self.width - self.socket.props.width
        else:
            self.text.props.x = self.socket.props.width + self.spacing

    def name(self):
        raise NotImplementedError

    def direction(self):
        raise NotImplementedError

    def canLink(self, other):
        raise NotImplementedError

class PadView(PadBaseView):

    __COLOR__ = "yellow"

    def __init__(self, pad):
        PadBaseView.__init__(self, pad)

    def direction(self):
        return self.pad.get_direction()

    def name(self):
        return self.pad.get_name()

    def canLink(self, other):
        return isinstance(other, gst.PadView)

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

class PadTemplateView(PadBaseView):

    def name(self):
        return self.pad.name_template

    def direction(self):
        return self.pad.direction

class RequestTemplateView(PadTemplateView):

    __COLOR__ = "blue"

    def canLink(self, other):
        return False

class SometimesTemplateView(PadTemplateView):

    __COLOR__ = "green"

def make_pad_view(pad):
    if isinstance(pad, gst.Pad):
        return PadView(pad)
    elif pad.presence == gst.PAD_REQUEST:
        return RequestTemplateView(pad)
    elif pad.presence == gst.PAD_SOMETIMES:
        return SometimesTemplateView(pad)
    return None

