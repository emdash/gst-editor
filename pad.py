from receiver import receiver, handler
import gst
import goocanvas
import controller
import view
import gtk
import utils
from point import Point
from link import Link

class PadBaseView(view.View, goocanvas.Group):

    spacing = 3

    __OUTLINE__ = "black"
    __FOCUS__ = "red"
    __HILIGHT__ = "black"

    class Controller(controller.Controller):

        __ARROW_COLOR__ = "red"

        arrow = goocanvas.Polyline(
            stroke_color = __ARROW_COLOR__)

        __center = None
        __prev_pads = []

        def enter(self, item, target):
            self._view.focus()

        def leave(self, item, target):
            self._view.unfocus()

        def drag_start(self):
            self._canvas.get_root_item().add_child(self.arrow)
            self.__center = self.center(self._view.socket)
            points = [self.__center, self.__center]
            self._mousedown = Point(0, 0)
            self.arrow.props.points = goocanvas.Points(points)

        def drag_end(self):
            self.arrow.remove()
            for pad in self.__prev_pads:
                pad.unhilight()
                if pad.canLink(self._view):
                    pad.linkPads(self._view)

        def __pads_under_point(self, (x, y)):
            items = self._canvas.get_items_in_area(
                goocanvas.Bounds(x - 1, y - 1, x + 1, y + 1), True, True, True)
            if items:
                return [item for item in items if isinstance(
                    item, PadBaseView)]
            return []

        def set_pos(self, obj, pos):
            points = [self.__center, pos]
            self.arrow.props.points = goocanvas.Points(points)
            for pad in self.__prev_pads:
                pad.unhilight()
            self.__prev_pads = self.__pads_under_point(pos)
            for pad in self.__prev_pads:
                if pad.canLink(self._view):
                    pad.hilight()


    def __init__(self, pad, element):
        self.pad = pad
        self.element = element
        goocanvas.Group.__init__(self)
        view.View.__init__(self)
        self.__createUi()
        self.links = []

    def __createUi(self):
        self.text = goocanvas.Text(
            font = "Sans 7",
            parent = self,
            text = self.name())

        self.socket = goocanvas.Rect(
            parent = self,
            width = 10,
            height = 10,
            fill_color = self.__COLOR__,
            stroke_color = self.__OUTLINE__)

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

    def linkPads(self, other):
        if self.direction() == gst.PAD_SRC:
            link = Link(self, other)
        else:
            link = Link(other, self)
        self.links.append(link)
        other.links.append(link)
        self.get_canvas().get_root_item().add_child(link)

    def updateLinks(self):
        for link in self.links:
            link.updateEndpoints()

    def hilight(self):
        self.socket.props.fill_color = self.__HILIGHT__

    def unhilight(self):
        self.socket.props.fill_color = self.__COLOR__

    def focus(self):
        self.socket.props.stroke_color = self.__FOCUS__

    def unfocus(self):
        self.socket.props.stroke_color = self.__OUTLINE__

class PadView(PadBaseView):

    __COLOR__ = "yellow"
    __BLOCKED__ = "dark yellow"

    def __init__(self, *args, **kwargs):
        PadBaseView.__init__(self, *args, **kwargs)
        self.block()

    def direction(self):
        return self.pad.get_direction()

    def name(self):
        return self.pad.get_name()

    def canLink(self, other):
        return ((not self.pad.is_linked()) and isinstance(other, PadView) and
            (self.pad.can_link(other.pad) or other.pad.can_link(self.pad)))

    # yes, we wan't this to be a static list
    blocked_pads = []

    @classmethod
    def unblock_all_pads(cls):
        for pad in cls.blocked_pads:
            pad.unblock()

    def block(self):
        self.pad.set_blocked_async(True, self.__block_cb)

    def unblock(self):
        self.pad.set_blocked_async(False, self.__block_cb)

    def __finish_pad_blocking(self, blocked):
        if blocked:
            self.blocked_pads.append(self)
            self.socket.props.fill_color = self.__BLOCKED__
        else:
            self.socket.props.fill_color = self.__NORMAL__
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

    class Controller(controller.Controller):

        def click(self, pos):
            self._view.props.parent.element.get_pad(
                self._view.pad.name_template)

        def set_pos(self, obj, pos):
            pass

    def canLink(self, other):
        return False

class SometimesTemplateView(PadTemplateView):

    __COLOR__ = "green"

    def canLink(self, other):
        return False

    def linkSrc(self, other):
        pass

    def linkSink(self, other):
        pass

def make_pad_view(pad, element):
    if isinstance(pad, gst.Pad):
        return PadView(pad, element)
    elif pad.presence == gst.PAD_REQUEST:
        return RequestTemplateView(pad, element)
    elif pad.presence == gst.PAD_SOMETIMES:
        return SometimesTemplateView(pad, element)
    return None

