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
from pipeline import PipelineView

if __name__ == "__main__":
    w = gtk.Window()
    n = gtk.Notebook()
    p = PipelineView(gst.Pipeline())
    w.add(n)
    w.connect("destroy", gtk.main_quit)
    w.show_all()
    gtk.main()
