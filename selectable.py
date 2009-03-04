import gtk
import view
import controller
import gobject
from receiver import receiver, handler


class Selection(object):

    def __init__(self):
        self.selected = set()

    def addToSelection(self, obj):
        self.setSelectionTo(self.selected | set([obj]))

    def removeFromSelection(self, obj):
        self.setSelectionTo(self.selected - set([obj]))

    def replaceSelection(self, obj):
        self.setSelectionTo(set([obj]))

    def clearSelection(self):
        self.setSelectionTo(set())

    def setSelectionTo(self, objs):
        old = self.selected
        self.selected = objs
        for obj in self.selected - old:
            obj.select()
        for obj in old - self.selected:
            obj.deselect()

    def delete(self):
        objs = list(self.selected)
        for obj in objs:
            obj.delete()

    def __iter__(self):
        return iter(self.selected)

class Controller(controller.Controller):

    def click(self, pos):
        if self._last_event.get_state() & gtk.gdk.SHIFT_MASK:
            self._view.addToSelection()
        elif self._last_event.get_state() & gtk.gdk.CONTROL_MASK:
            self._view.removeFromSelection()
        else:
            self._view.replaceSelection()

    def set_pos(self, obj, pos):
        controller.Controller.set_pos(self, obj, pos)
        if self._view.selection:
            deltas = ((obj, self.pos(obj) - self.pos(self._view)) for obj in
                self._view.selection if obj is not self._view)
            for obj, delta in deltas:
                obj.set_pos(pos + delta)

class Selectable(view.View):

    Controller = Controller

    def __init__(self, selection):
        view.View.__init__(self)
        self.selection = selection

    def replaceSelection(self):
        if self.selection:
            self.selection.replaceSelection(self)

    def addToSelection(self):
        if self.selection:
            self.selection.addToSelection(self)

    def removeFromSelection(self):
        if self.selection:
            self.selection.removeFromSelection(self)

    def select(self):
        pass

    def deselect(self):
        pass

    def delete(self):
        pass

    def set_pos(self, (x, y)):
        self.set_simple_transform(x, y, 1.0, 0)
