#!/usr/bin/env python
import gobject
gobject.threads_init()
import gtk
import os.path
import gst
from pipeline import PipelineView

if __name__ == "__main__":
    w = gtk.Window()
    p = PipelineView(gst.Pipeline())
    w.add(p)
    w.connect("destroy", gtk.main_quit)
    w.show_all()
    gtk.main()
