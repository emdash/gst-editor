#Copyright (C) 2008 Brandon J. Lewis
#
#License:
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2 of the License, or (at your option) any later version.
#
#    This package is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this package; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
#
#On Debian systems, the complete text of the GNU Lesser General
#Public License can be found in `/usr/share/common-licenses/LGPL'.

import gobject
gobject.threads_init()
import goocanvas
import gtk
import pango

## GTK Conveinence Functions

def printall(*args):
    print args

def null_func(*args):
    pass

def widget_helper(klass, func=None, *args, **kwargs):
    """Used to create convenience functions like scrolled()"""
    def retfunc(*children):
        ret = klass(*args, **kwargs)
        for child in children:
            if func:
                func(ret, child)
            else:
                ret.add(child)
        return ret
    return retfunc

def container_helper(klass, *args, **kwargs):
    """Used to create convinience functions like HBox() and VBox()"""
    def childfunc(container, child):
        widget, end, expand, fill = child
        if end == 'end':
            container.pack_end(widget, expand, fill)
        elif end == 'start':
            container.pack_start(widget, expand, fill)
        else:
            container.add(widget)
    return widget_helper(klass, childfunc, *args, **kwargs)

scrolled = widget_helper(gtk.ScrolledWindow)
viewport = widget_helper(gtk.Viewport)
hbox = container_helper(gtk.HBox)
hbuttonbox = widget_helper(gtk.HButtonBox)
vbuttonbox = widget_helper(gtk.VButtonBox)
vbox = container_helper(gtk.VBox)
vpane = widget_helper(gtk.VPaned)
hpane = widget_helper(gtk.HPaned)

def get_text_dimensions(text):
    ink, logical = text.get_natural_extents()
    x1, y1, x2, y2 = [pango.PIXELS(x) for x in logical]
    return x2 - x1, y2 - y1
