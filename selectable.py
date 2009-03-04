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

    def setSelectionTo(self, objs):
        old = self.selected
        self.selected = objs
        for obj in self.selected - old:
            obj.select()
        for obj in old - self.selected:
            obj.deselect()

    def __iter__(self):
        return iter(self.selected)

class SelectableController(controller.Controller):

    def click(self, pos):
        if self._last_event.get_state() & gtk.gdk.SHIFT_MASK:
            self._view.addToSelection()
        elif self._last_event.get_state() & gtk.gdk.CONTROL_MASK:
            self._view.removeFromSelection()
        else:
            self._view.replaceSelection()

class Selectable(view.View):

    Controller = SelectableController

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
