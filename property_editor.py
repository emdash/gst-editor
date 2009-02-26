# PiTiVi , Non-linear video editor
#
#       ui/gstwidget.py
#
# Copyright (c) 2005, Edward Hervey <bilboed@bilboed.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

"""
Widget for gstreamer element properties viewing/setting
"""

import gobject
import gtk
import gst
from gettext import gettext as _

def get_widget_propvalue(prop, widget):
    """ returns the value of the given propertywidget """
    # FIXME : implement the case for flags
    type_name = gobject.type_name(prop.value_type.fundamental)

    if (type_name == 'gchararray'):
        return widget.get_text()
    if (type_name in ['guint64', 'gint64', 'gint', 'gulong']):
        return widget.get_value_as_int()
    if (type_name in ['gfloat']):
        return widget.get_value()
    if (type_name in ['gboolean']):
        return widget.get_active()
    if type_name in ['GEnum']:
        return widget.get_model()[widget.get_active()][1]
    return None

def make_property_widget(unused_element, prop, value=None):
    """ Creates a Widget for the given element property """
    # FIXME : implement the case for flags
    type_name = gobject.type_name(prop.value_type.fundamental)

    if value == None:
        value = prop.default_value
    if (type_name == 'gchararray'):
        widget = gtk.Entry()
        widget.set_text(str(value))
    elif (type_name in ['guint64', 'gint64', 'guint', 'gint', 'gfloat', 'gulong']):
        widget = gtk.SpinButton()
        if type_name == 'gint':
            widget.set_range(-(2**31), 2**31 - 1)
        elif type_name == 'guint':
            widget.set_range(0, 2**32 - 1)
        elif type_name == 'gint64':
            widget.set_range(-(2**63), 2**63 - 1)
        elif type_name in ['gulong', 'guint64']:
            widget.set_range(0, 2**64 - 1)
        elif type_name == 'gfloat':
            widget.set_range(0.0, 2**64 - 1)
            widget.set_digits(5)
        widget.set_value(float(value))
    elif (type_name == 'gboolean'):
        widget = gtk.CheckButton()
        if value:
            widget.set_active(True)
    elif (type_name == 'GEnum'):
        model = gtk.ListStore(gobject.TYPE_STRING, prop.value_type)
        widget = gtk.ComboBox(model)
        cell = gtk.CellRendererText()
        widget.pack_start(cell, True)
        widget.add_attribute(cell, 'text', 0)

        idx = 0
        for key, val in prop.enum_class.__enum_values__.iteritems():
            gst.log("adding %s / %s" % (val.value_name, val))
            model.append([val.value_name, val])
            if val == value:
                selected = idx
            idx = idx + 1
        widget.set_active(selected)
    else:
        widget = gtk.Label(type_name)
        widget.set_alignment(1.0, 0.5)

    if not prop.flags & gobject.PARAM_WRITABLE:
        widget.set_sensitive(False)
    return widget

class PropertyEditor(gtk.VBox):
    """
    Widget to view/modify properties of a gst.Element
    """

    def __init__(self):
        gtk.VBox.__init__(self)
        self.element = None
        self.ignore = None
        self.properties = None

    def setElement(self, element, properties={}, ignore=['name']):
        """ Set given element on Widget, with optional properties """
        gst.info("element:%s, properties:%s" % (element, properties))
        self.element = element
        self.ignore = ignore
        self.properties = {} #key:name, value:widget
        self._addWidgets(properties)

    def _addWidgets(self, properties):
        props = [x for x in gobject.list_properties(self.element) if not x.name in self.ignore]
        if not props:
            self.pack_start(gtk.Label("No properties..."))
            self.show_all()
            return
        table = gtk.Table(rows=len(props), columns=2)
        table.set_row_spacings(5)
        table.set_col_spacings(5)
        table.set_border_width(5)
        y = 0
        for prop in props:
            label = gtk.Label(prop.nick)
            label.set_alignment(0.0, 0.5)
            widget = make_property_widget(self.element, prop, properties.get(prop.name))
            table.attach(label, 0, 1, y, y+1, xoptions=gtk.FILL, yoptions=gtk.FILL)
            table.attach(widget, 1, 2, y, y+1, yoptions=gtk.FILL)
            self.properties[prop] = widget
            y += 1
        self.pack_start(table)
        self.show_all()

    def getSettings(self):
        """ returns the dictionnary of propertyname/propertyvalue """
        d = {}
        for prop, widget in self.properties.iteritems():
            if not prop.flags & gobject.PARAM_WRITABLE:
                continue
            value = get_widget_propvalue(prop, widget)
            if not value == None:
                d[prop.name] = value
        return d
