import gst
import goocanvas
from receiver import receiver, handler
from element import ElementView

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

