import goocanvas
import gobject
import view
import controller
from receiver import receiver, handler
import gst

class Link(view.View, goocanvas.Polyline):

    class Controller(controller.Controller):

        def enter(self, item, target):
            self._view.hilight()

        def leave(self, item, target):
            self._view.unhilight()

    def __init__(self, src, sink):
        goocanvas.Polyline.__init__(self)
        view.View.__init__(self)
        self.src = src
        self.sink = sink
        self.srcpad = src.pad
        self.sinkpad = sink.pad
        self.props.stroke_color = "red"
        self.props.line_width = 2.0
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
            self.props.visibility = goocanvas.ITEM_VISIBLE
            self.updateEndpoints()
        else:
            self.props.visibility = goocanvas.ITEM_INVISIBLE

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
