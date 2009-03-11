import goocanvas
import gobject
import view
import controller
from receiver import receiver, handler
import gst
import selectable

class Link(selectable.Selectable, goocanvas.Polyline):

    class Controller(selectable.Controller):

        def enter(self, item, target):
            self._view.hilight()

        def leave(self, item, target):
            self._view.unhilight()

        def set_pos(self, item, target):
            pass

    def __init__(self, src, sink, selection):
        goocanvas.Polyline.__init__(self)
        selectable.Selectable.__init__(self, selection)
        self.src = src
        self.sink = sink
        self.srcpad = src.pad
        self.sinkpad = sink.pad
        self.props.stroke_color = "black"
        self.props.line_width = 2.0
        self.props.end_arrow = True
        self.checkVisibility()
        self.link()

    def link(self):
        self.src.unblock()
        self.sink.unblock()
        try:
            self.srcpad.link(self.sinkpad)
        except gst.LinkError:
            self.src.block()
            self.sink.block()

    def unlink(self):
        pass

    def select(self):
        self.props.stroke_color = "red"

    def deselect(self):
        self.props.stroke_color = "black"

    def delete(self):
        if not (self.srclinked or self.sinklinked):
            self._unlink()

    def _unlink(self):
        self.src.unlink(self)
        self.sink.unlink(self)
        self.src = None
        self.sink = None
        self.remove()

    def set_pos(self, pos):
        pass

    def hilight(self):
        self.props.line_width = 3.0

    def unhilight(self):
        self.props.line_width = 2.0

    def updateEndpoints(self):
        if self.src and self.sink:
            b = self.src.socket.get_bounds()
            start = (b.x1 + b.x2) / 2, (b.y1 + b.y2) / 2
            b = self.sink.socket.get_bounds()
            end = (b.x1 + b.x2) / 2, (b.y1 + b.y2) / 2
            self.props.points = goocanvas.Points([start, end])

    def checkVisibility(self):
        if self.srclinked and self.sinklinked:
            self.props.line_dash = goocanvas.LineDash([])
            self.updateEndpoints()
        else:
            self.props.line_dash = goocanvas.LineDash([3.0, 3.0])
        return False

    srcpad = receiver()
    sinkpad = receiver()
    srclinked = False
    sinklinked = False

    @handler(srcpad, "linked")
    def srcLinked(self, pad, target):
        self.srclinked = True
        self.checkVisibility()

    @handler(srcpad, "unlinked")
    def srcUnlinked(self, pad, target):
        self.srclinked = False
        gobject.idle_add(self.checkVisibility)

    @handler(sinkpad, "linked")
    def sinkLinked(self, pad, target):
        self.sinklinked = True
        gobject.idle_add(self.checkVisibility)

    @handler(sinkpad, "unlinked")
    def sinkUnlinked(self, pad, target):
        self.sinklinked = False
        gobject.idle_add(self.checkVisibility)
