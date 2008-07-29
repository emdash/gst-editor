#Copyright (C) 2008 Brandon J. Lewis
#
#License:
#
#    This program is free software; you can redistribute it and/or
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
#Public License can be found in `/usr/share/common-licenses/LGPL'.

"""Experimental noun-verb gst editor interface"""
import gobject
gobject.threads_init()
import gst
import goocanvas
import pygtk
pygtk.require("2.0")
import gtk
from itertools import izip
from goocanvashelper import *

#TODO: load from xml files

WIN_SIZE = (400, 360)

element_box = (goocanvas.Rect,
    {
        "fill_color" : "grey",
        "radius_y" : 5,
        "radius_x" : 5,
    },
    {
        "normal_color" : "grey",
        "active_color" : "blue",
        "selected_color": "red",
        "deselected_color" : "black",
    }
)

element_text = (Text,
    {
        "font" : "Sans 9",
        "text" : "An Element",
        "width" : 100,
        "height" : 30,
    },
    {},
)

element_pad = (goocanvas.Rect,
    {
        "width" : 10,
        "height" : 10,
        "fill_color" : "green",
        "stroke_color" : "black",
    },
    {
        "normal_color" : 0xFFFF00FF,
        "blocked_color" : 0xAAAA00FF,
        "active_color" : "red"
    }
)

pad_text = (Text,
    {
        "anchor" : gtk.ANCHOR_NORTH_WEST,
        "font" : "Sans 8",
        "text" : "A Pad",
        "width" : 40,
        "height" : 15,
    },
    {},
)

link_arrow = (goocanvas.Polyline,
    {
        "stroke_color" : "red",
        "end_arrow": "true",
    },
    {
    }
)

link_tool = (goocanvas.Polyline,
    {
        "stroke_color"  : "red",
        "line_dash" : goocanvas.LineDash([1.5, 1.5])
    },
    {}
)

# our selection box is a translucent blue rectangle with 
# a light blue outline
selection_box = (goocanvas.Rect,
    {
        "stroke_color_rgba" : 0x33CCFF66,
        "fill_color_rgba" : 0x33CCFF66,
    },
    {
    }
)

target = [
    ('GST_ELEMENT_NAME', 0, 0)
]

def str_widget(prop):
    return (gtk.Entry(), "changed", gtk.Entry.get_text, 
        gtk.Entry.set_text)

def num_widget(prop):
    ret = (gtk.HScale(), "value-changed", gtk.HScale.get_value,
        gtk.HScale.set_value)
    minimum = float("-Infinity")
    maximum = float("Infinity")
    if hasattr(prop, "minimum"):
        minimum = prop.minimum
    if hasattr(prop, "maximum"):
        maximum = prop.maximum
    ret[0].set_range(minimum, maximum)
    return ret

def choice_widget(prop):
    if hasattr(prop, "_getChoices"):
        return (gtk.ComboBox(prop._getChoices()), "changed",
            gtk.ComboBox.get_active, gtk.ComboBox.set_active)
    else:
        return str_widget(prop)

def bool_widget(prop):
    return (gtk.CheckButton(), "toggled", gtk.CheckButton.get_active,
        gtk.CheckButton.set_active)

def file_widget(prop):
    return (gtk.FileChooserButton("File"), "selection-changed", 
        gtk.FileChooserButton.get_filename,
            gtk.FileChooserButton.set_filename)

def method_widget(prop):
    ret = gtk.combo_box_new_text()
    for m in ["solid", "green", "blue", "custom"]:
        ret.append_text(m)
    return (ret, "changed", gtk.ComboBox.get_active, 
        gtk.ComboBox.set_active)

def pattern_widget(prop):
    ret = gtk.combo_box_new_text()
    for m in ["smpte", "snow", "black", "white", "red", "green", "blue",
        "checkers-1", "checkers-2", "checkers-4", "checkers-8",
        "circular", "blink"]:
        ret.append_text(m)
    return (ret, "changed", gtk.ComboBox.get_active, 
        gtk.ComboBox.set_active)

name_widgets = {
    "location" : file_widget,
    "method" : method_widget,
    "pattern" : pattern_widget,
}

prop_widgets = {
    gobject.TYPE_STRING : str_widget,
    gobject.TYPE_DOUBLE : num_widget,
    gobject.TYPE_FLOAT : num_widget,
    gobject.TYPE_ENUM : choice_widget,
    gobject.TYPE_INT : num_widget,
    gobject.TYPE_UINT : num_widget,
    gobject.TYPE_LONG : num_widget,
    gobject.TYPE_ULONG : num_widget,
    gobject.TYPE_BOOLEAN : bool_widget,
}

def widget_lookup(prop):
    if name_widgets.has_key(prop.name):
        return name_widgets[prop.name](prop)
    elif prop_widgets.has_key(prop.value_type):
        return prop_widgets[prop.value_type](prop)
    elif hasattr(prop, "enum_class"):
        return choice_widget(prop)
    elif hasattr(prop, "minimum") or hasattr(prop, "maximum"):
        return num_widget(prop)
    #pick a random signal here, because we need to connect to something
    return (gtk.Label("Unsupported"), "copy-clipboard", null_func,
        null_func)

## App-Specific Functions

class LinkError(Exception):
    pass

blocked_pads = []

def block_pad(pad):
    global blocked_pads
    def pad_blocked(pad):
        blocked_pads.append(pad)
    pad.set_blocked_async(true, pad_blocked)

def unblock_pad(pad):
    global blocked_pads
    def pad_unblocked(pad):
        blocked_pads.remove(pad)
    pad.set_blocked_async(false, pad_unblocked)

def unblock_all_pads(pad):
    global blocked_pads
    for pad in blocked_pads:
        unblock_pad(pad)


def update_link_start(pos, item):
    """internal callback of an experimental feature"""
    arrow = item.get_data("link_arrow")
    end = center(item.get_data("linked"))
    arrow.props.points = goocanvas.Points([center(item), end])

def update_link_end(pos, item):
    """internal callback of an experimental feature"""
    arrow = item.get_data("link_arrow")
    start = center(item.get_data("linked"))
    arrow.props.points = goocanvas.Points([start, center(item)])

def link_objects(canvas, a, b):
    """Link canvas items a, b with goocanvas.Polyline arrow.
    If a or b move, the endpoints of the arrow are updated"""
    a.set_data("linked", b)
    b.set_data("linked", a)
    arrow = make_item(link_arrow)
    arrow.props.points = goocanvas.Points([center(a), center(b)])
    canvas.get_root_item().add_child(arrow)
    a.set_data("link_arrow", arrow)
    b.set_data("link_arrow", arrow)
    pos_change(a, update_link_start)
    pos_change(b, update_link_end)
    return False

def unlink_objects(obj):
    """Break the link between obj and any item to which it is linked,
    and remove the arrow from the canvas"""
    arrow = obj.get_data("link_arrow")
    linked = obj.get_data("linked")
    arrow.remove()
    obj.set_data("link_arrow", None)
    linked.set_data("link_arrow", None)
    obj.set_data("linked", None)
    linked.set_data("linked", None)
    unlink_pos_change(obj)
    unlink_pos_change(linked)
    return False

def link_start(item, target, event, canvas, break_cb):
    """Internal callback to an experimental feature"""
    start = center(item)
    linked = item.get_data("linked")
    if linked:
        break_cb(item, linked)
        return True
    arrow = make_item(link_tool)
    item.set_data("link_arrow", arrow)
    item.set_data("linking", True)
    item.set_data("link_start", start)
    canvas.get_root_item().add_child(arrow)
    return True

def link_end(item, target, event, canvas, make_cb):
    """Internal callback to an experimental feature"""
    arrow = item.get_data("link_arrow")
    if item.get_data("linking"):
        x, y = event_coords(canvas, event)
        item.set_data("linking", False)
        found = canvas.get_items_at(x, y, False)
        if not found:
            return True
        for f in found:
            if f.get_data("linkable"):
                make_cb(item, f)
    if arrow:
        arrow.remove()
    #item.set_data("link_arrow", None)
    return True

def update_link_indicator(item, target, event, canvas, widget):
    """Internal callback to an experimental feature"""
    if widget.get_data("linking"):
        start = widget.get_data("link_start")
        if start:
            end = event_coords(canvas, event)
            arrow = widget.get_data("link_arrow")
            points = goocanvas.Points([start, end])
            arrow.props.points = points
        return True
    return False

def make_linkable(canvas, item, make_cb, break_cb):
    """Experimental feature: don't use this""" 
    def test(*anything):
        return False
    item.set_data("linkable", True)
    item.set_data("link_start", None)
    item.connect("button_press_event", link_start, canvas, break_cb)
    item.connect("button_release_event", link_end, canvas, make_cb)
    canvas.get_root_item().connect("motion_notify_event", 
        update_link_indicator, canvas, item)


def link_pads(src, sink):
    src_pad = src.get_data("pad")
    sink_pad = sink.get_data("pad")
    src_pad.set_blocked_async(False, block_pad_cb)
    sink_pad.set_blocked_async(False, block_pad_cb)
    if not (src_pad.is_linked() or sink_pad.is_linked()):
        if src_pad.can_link(sink_pad):
            try:
                print "link: %r -> %r" % (src_pad, sink_pad)
                src_pad.link(sink_pad)
            except gst.LinkError, e:
                print e.message
                print "could not link %r to %r" % (src_pad, sink_pad)
                src_pad.set_blocked_async(True, block_pad_cb)
                sink_pad.set_blocked_async(True, block_pad_cb)

def unlink_pads(src, sink):
    src = src.get_data("pad").get_parent_element()
    sink = sink.get_data("pad").get_parent_element()
    src.unlink(sink)

def make_template_widget(canvas, pad, parent):
    def enter(item, target, event):
        state[0] = True
        if state[1]:
            box.props.fill_color_rgba = 0x333399FF
        
    def leave(item, trget, event):
        state[0] = False
        if state[1]:
            box.props.fill_color = "blue"

    def down(item, target, event):
        box.props.fill_color_rgba = 0x333399FF
        state[1] = True

    def up(item, target, event):
        box.props.fill_color = "blue"
        state[1] = False
        if state[0]:
            # item has been clicked
            print "requesting new pad %s" % pad.name_template
            parent.get_pad(pad.name_template)

    state = [False, False]
    box = make_item(element_pad)
    text = make_item(pad_text)
    box.props.fill_color = "blue"
    direction = pad.direction
    if direction == gst.PAD_SINK:
        ret = hlist(box, text)
    elif direction == gst.PAD_SRC:
        ret = hlist(text, box)
    ret.set_data("direction", direction)
    ret.set_data("pad", pad)
    state = [False, False]

    text.props.text = pad.name_template
    box.connect("enter_notify_event", enter)
    box.connect("leave_notify_event", leave)
    box.connect("button_press_event", down)
    box.connect("button_release_event", up)
    return ret

def make_pad_widget(canvas, pad, parent):

    def linked_cb(pad, target):
        src = pad.get_data("box")
        sink = target.get_data("box")
        print "link created: %r -> %r" % (pad, target)
        gobject.idle_add(link_objects, canvas, src, sink)

    def unlinked_cb(pad, target):
        src = pad.get_data("box")
        pad.set_blocked_async(True, block_pad_cb)
        target.set_blocked_async(True, block_pad_cb)
        gobject.idle_add(unlink_objects, src)

    box = make_item(element_pad)
    text = make_item(pad_text)
    box.props.fill_color = "yellow"
    direction = pad.get_direction()
    if direction == gst.PAD_SINK:
        ret = hlist(box, text)
    elif direction == gst.PAD_SRC:
        pad.connect("linked", linked_cb)
        pad.connect("unlinked", unlinked_cb)
        ret = hlist(text, box)
    ret.set_data("direction", direction)
    ret.set_data("pad", pad)
    box.set_data("parent_element", parent)
    box.set_data("pad", pad)
    box.set_data("direction", direction)
    pad.set_data("widget", ret)
    print pad.get_data("widget")
    pad.set_data("box", box)
    text.props.text = pad.get_name()
    make_linkable(canvas, box, link_pads, unlink_pads)
    return ret

def make_property_editor():
    def make_prop_widget(prop, elements):
        def changed_cb(object, elements):
            for element in elements:
                element.set_property(prop.name, get_val(widget))
        if (prop.flags & gobject.PARAM_WRITABLE):
            widget, signal, get_val, set_val = (
                widget_lookup(prop))
            if len(elements) == 1:
                pval = elements[0].get_property(prop.name)
                if pval:
                    set_val(widget, pval)
            widget.connect(signal, changed_cb, elements)
        else:
            widget = gtk.HBox()
        widget.set_size_request(100, 30)
        return widget
    
    def update(elements):
        # clear old property widgets
        for c in props.get_children():
            c.hide()
            props.remove(c)
        # find the intersection of all selected properties
        element_props = [set([p for p in el.props]) 
            for el in elements]
        if element_props:
            element_props = reduce(lambda a, b : a.intersection(b),
                element_props)
            for prop in element_props:
                widget = make_prop_widget(prop, elements)
                label = gtk.Label(prop.name)
                label.set_size_request(75, 0)
                props.pack_start(
                    hbox((label, "start", True, True),
                         (widget, "end", True, True)), True, False)
        props.show_all()

    props = vbox()
    ret = vbox((gtk.Label("Properties"), 'start', True, True),
        (props, "start", True, True))
    x = scrolled()
    x.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
    x.add_with_viewport(ret)

    return x, update

def block_pad_cb(pad, state):
    def inner(pad, state):
        print "blocking pad: %r" % pad
        widget = pad.get_data("box")
        color = "blocked_color" if state else "normal_color"
        widget.props.fill_color_rgba = widget.get_data(color)
        return False
    gobject.idle_add(inner, pad, state)

def make_element_widget(canvas, element):
    def add_pad_widget(pad_widget):
        d = pad_widget.get_data("direction")
        if d == gst.PAD_SRC:
            source_pads.add_child(pad_widget)
        else:
            sink_pads.add_child(pad_widget)

    def show_pad(pad):
        w = make_pad_widget(canvas, pad, element)
        pad.set_blocked_async(True, block_pad_cb)
        add_pad_widget(w)
        return False

    def pad_added(element, pad):
        print pad.get_name(), pad.get_caps()
        gobject.idle_add(show_pad, pad)

    def hide_pad(pad):
        if pad.get_direction() == gst.PAD_SRC:
            source_pads.remove_child(pad.get_data("widget"))
        else:
            sink_pads.remove_child(pad.get_data("widget"))
        return False

    def pad_removed(element, pad):
        print pad.get_name(), pad.get_direction(), pad
        gobject.idle_add(hide_pad, pad)


    background = make_item(element_box)
    text = make_item(element_text)
    text.props.text = element.get_name()
    source_pads = vlist(goocanvas.Rect(width=55))
    sink_pads = vlist(goocanvas.Rect(width=55))
    content = vlist(text, hlist(sink_pads, source_pads))
    size_change(content, lambda size_: set_size(background, size_))
    ret = group(background, content)
    ret.set_data("element", element)
    ret.set_data("box", background)
    background.set_data("element", element)
    make_selectable(canvas, ret)
    make_dragable(canvas, ret, lambda pos_: (max(0, pos_[0]), max(0, pos_[1])))

    for pad in element.get_pad_template_list():
        if pad.presence == gst.PAD_REQUEST:
            add_pad_widget(make_template_widget(canvas, pad, element))

    for pad in element.pads():
        show_pad(pad)

    element.connect("pad-added", pad_added)
    element.connect("pad-removed", pad_removed)
    element.set_data("widget", ret)
    return ret

def make_canvas(pipeline, sel_changed_cb):
    def element_added(bin, element):
        x, y = coords[element]
        w = make_element_widget(canvas, element)
        set_pos(w, (x, y))
        root.add_child(w)

    def element_removed(bin, element):
        widget = element.get_data("widget")
        widget.remove()

    def add_element(element, x, y):
        el = gst.element_factory_make(element)
        coords[el] = (x, y)
        pipeline.add(el)
        return True

    def dup_element(button):
        for obj in canvas.get_data("selected_objects"):
            factory = obj.get_data("element").get_factory().get_name()
            element = gst.element_factory_make(factory)
            coords[element] = point_sum(pos(obj), (30, 100))
            pipeline.add(element)

    def remove_element(button):
        for obj in canvas.get_data("selected_objects"):
            pipeline.remove(obj.get_data("element"))
        set_selection(canvas, set())

    def drag_data_received(w, context, x, y, data, info, time):
        context.finish(True, False, time)
        add_element(data.data, *pixel_coords(canvas, (x, y)))

    def sel_cb(selected, deselected):
        for obj in selected:
            obj = obj.get_data("box")
            obj.props.stroke_color = obj.get_data("selected_color")
        for obj in deselected:
            obj = obj.get_data("box")
            obj.props.stroke_color = obj.get_data("deselected_color")
        sel_changed_cb([obj.get_data("element") for obj in selected])

    coords = {}
    canvas = goocanvas.Canvas()
    canvas.set_size_request(*WIN_SIZE)
    canvas.drag_dest_set(gtk.DEST_DEFAULT_ALL, target
        , gtk.gdk.ACTION_COPY)
    canvas.connect("drag_data_received", drag_data_received)
    manage_selection(canvas, make_item(selection_box), True, sel_cb)
    root = canvas.get_root_item()
    pipeline.connect("element_added", element_added)
    pipeline.connect("element_removed", element_removed)

    return canvas, (
        ("Delete", remove_element, ()),
        ("Duplicate", dup_element, ()),
    )

def make_browser():
    def get_data(w, context, s_d, info, time):
        row = w.get_cursor()[0][0]
        s_d.set(s_d.target, 8, treemodel[row][1])
        
    # get list of all elements
    registry = gst.registry_get_default()
    registrylist = registry.get_feature_list(gst.ElementFactory)
    registrylist.sort(lambda x, y: cmp(x.get_name(), y.get_name()))    
    
    # create a tree view to display them
    treemodel = gtk.TreeStore(gobject.TYPE_PYOBJECT, gobject.TYPE_STRING)
    for item in registrylist:
        treemodel.append(None, [item, item.get_name()])
    treeview = gtk.TreeView()
    treeview.set_model(treemodel)
    renderer = gtk.CellRendererText()
    column = gtk.TreeViewColumn("Element", renderer, text=1)
    treeview.append_column(column)
    treeview.set_size_request(100, 100)
    treeview.drag_source_set(gtk.gdk.BUTTON1_MASK,
        target, gtk.gdk.ACTION_COPY)
    treeview.connect('drag_data_get', get_data)
    return scrolled(treeview)

gst_states = (
    (gst.STATE_PAUSED, "Paused"),
    (gst.STATE_READY, "Ready"),
    (gst.STATE_PLAYING, "Playing")
)

def make_buttons(pipeline, commands):
    def button(label, callback, data):
        ret = gtk.Button(label)
        ret.connect("clicked", callback, *data)
        return ret

    def radio(label, callback, data):
        ret = gtk.Button(label)
        ret.connect("clicked", callback, data)
        return ret

    def set_state(button, state):
        pipeline.set_state(state)
        return True
    
    def null_cb(button):
        set_state(None, gst.STATE_NULL)
        for b in buttons.values():
            b.set_sensitive(True)

    def message_handler(bus, message):
        if message.type == gst.MESSAGE_EOS:
            print "eos message"
        if message.type == gst.MESSAGE_STATE_CHANGED:
            old, new, pending = message.parse_state_changed()
            if old != gst.STATE_NULL:
                buttons[old].set_sensitive(True)
            if new != gst.STATE_NULL:
                buttons[new].set_sensitive(False)
        elif message.type == gst.MESSAGE_ERROR:
            print message.parse_error()
        elif message.type == gst.MESSAGE_WARNING:
            print message.parse_warning()

    box = gtk.HButtonBox()
    for data in commands:
        box.add(button(*data))
    
    null = gtk.Button("NULL")
    null.connect("clicked", null_cb)
    box.add(null)
    buttons = {}
    for state, label in gst_states:
        cur = radio(label, set_state,state)
        box.add(cur)
        buttons[state] = cur

    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", message_handler)
    return box

def editor(pipeline):
    props, update = make_property_editor()
    canvas, commands = make_canvas(pipeline, update)
    return hpane(vpane(make_browser(), props),
        vbox((make_buttons(pipeline, commands), 'start', False, False),
            (scrolled(canvas), 'start', True, True)))

if __name__ == '__main__':
    p = gst.Pipeline()
    w = gtk.Window()
    w.add(editor(p))
    w.show_all()
    w.connect("destroy", gtk.main_quit)
    gtk.main()
