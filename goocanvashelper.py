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

## GooCanvas Convenience Functions

class smartgroup(goocanvas.Group):
    """Extends goocanvas.Group() with 
    through gobject properties x, y, and width/height"""
    __gtype_name__ = 'SmartGroup'

    x = gobject.property(type=float, default=0)
    y = gobject.property(type=float, default=0)
    width = gobject.property(type=float, default=0)
    height = gobject.property(type=float, default=0)

    def __init__(self, *args, **kwargs):
        goocanvas.Group.__init__(self, *args, **kwargs)
        self.children = {}
        self.signals = {}
        self.connect("notify::x", self.move_x_children)
        self.connect("notify::y", self.move_y_children)

    def move_x_children(self, object, prop):
        for child, (x, y) in self.children.items():
            child.set_property('x', self.x + x)

    def move_y_children(self, object, prop):
        for child, (x, y) in self.children.items():
            child.set_property('y', self.y + y)

    def update_width(self, obj, prop):
        def compute(c, p):
            return (c.get_property('width') + p[0])
        widths = (compute(c, p) for c, p in self.children.items())
        self.width = max(widths) if len(self.children) else float(0)

    def update_height(self, obj, prop):
        def compute(c, p):
            return (c.get_property('height') + p[1])
        heights = (compute(c, p) for c, p in self.children.items())
        self.height = max(heights) if len(self.children) else float(0)

    def set_child_pos(self, child, pos_):
        set_pos(child, point_sum(pos(self), pos_))
        self.children[child] = pos_

    def add_child(self, child, p=None):
        goocanvas.Group.add_child(self, child)
        cw = child.connect("notify::width", self.update_width)
        ch = child.connect("notify::height", self.update_height)
        self.signals[child] = (cw, ch)
        if not p:
            self.children[child] = pos(child)
        else:
            self.set_child_pos(child, p)
        self.update_width(None, None)
        self.update_height(None, None)

    def remove_child(self, child):
        goocanvas.Group.remove_child(self, child)
        for s in self.signals[child]:
            child.disconnect(s)
        del self.children[child]
        self.update_width(None, None)
        self.update_height(None, None)

class List(smartgroup):
    __gytpe_name__ = 'List'

    #TODO: changing this property should force update of list
    spacing = gobject.property(type=float)

    def __init__(self, spacing=5.0, *args, **kwargs):
        smartgroup.__init__(self, *args, **kwargs)
        self.cur_pos = 0
        self.spacing = spacing
        self.order = []

    def compact(self):
        cur = 0
        for child in self.order:
            self.set_child_pos(child, self.cur(cur))
            cur += self.spacing + height(child)
        self.cur_pos = cur
    
    def remove_child(self, child):
        smartgroup.remove_child(self, child)
        self.order.remove(child)
        self.compact()

    def add_child(self, child):
        smartgroup.add_child(self, child, self.cur(self.cur_pos))
        self.cur_pos += self.spacing + self.dimension(child)
        self.order.append(child)

    def add(self, child):
        self.add_child(child)

    def insert_child(self, child, index):
        smartgroup.add_child(self, child, self.cur(self.cur_pos))
        self.order.insert(child, index)
        self.compact()

class VList(List):
    __gtype_name__ = 'VList'

    def __init__(self, *args, **kwargs):
        List.__init__(self, *args, **kwargs)
    
    def cur(self, value):
        return (0, value)

    def dimension(self, child):
        return height(child)

class HList(List):
    __gtype_name__ = 'HList'

    def __init__(self, *args, **kwargs):
        List.__init__(self, *args, **kwargs)

    def cur(self, value):
        return (value, 0)

    def dimension(self, child):
        return width(child)

vlist = widget_helper(VList)
hlist = widget_helper(HList)

## canvas item wrappers
class Text(goocanvas.Text):
    '''adds the "missing" height property to goocanvas.Text'''
    #TODO: width/height are dumy props in this class...they 
    #should ideally be read-only values calculated from the layout
    #parameters and text. 
    __gtype_name__ = 'SmartText'

    height = gobject.property(type=float, default=0)
    width = gobject.property(type=float, default=0)

    def __init__(self, *args, **kwargs):
        goocanvas.Text.__init__(self, *args, **kwargs)

def event_coords(canvas, event):
    """returns the coordinates of an event"""
    return canvas.convert_from_pixels(event.x, event.y)

def point_difference(p1, p2):
    """Returns the 2-dvector difference p1 - p2"""
    p1_x, p1_y = p1
    p2_x, p2_y = p2
    return (p1_x - p2_x, p1_y - p2_y)

def point_sum(p1, p2):
    """Returns the 2d vector sum p1 + p2"""
    p1_x, p1_y = p1
    p2_x, p2_y = p2
    return (p1_x + p2_x, p1_y + p2_y)

def point_mul(factor, point):
    """Returns a scalar multiple factor * point"""
    return tuple(factor * v for v in point)

def pos(item):
    """Returns a tuple x, y representing the position of the 
    supplied goocanvas Item"""
    return item.props.x, item.props.y

def pos_change_cb(item, prop, callback, data):
    callback(pos(item), item, *data)

def size_change_cb(item, prop, callback):
    callback(size(item))

def pos_change(item, callback, *data):
    """Connects the callback to the x and y property notificaitons.
    Do not call this function again without calling unlink_pos_change()
    first"""
    item.set_data("x_sig_hdl", item.connect("notify::x", pos_change_cb,
        callback, data))
    item.set_data("y_sig_hdl", item.connect("notify::y", pos_change_cb,
        callback, data))

def unlink_pos_change(item):
    """Disconnects signal handlers after calling pos_change()"""
    item.disconnect(item.get_data("x_sig_hdl"))
    item.disconnect(item.get_data("y_sig_hdl"))

def size(item):
    """Returns the tuple (<width>, <height>) of item"""
    return item.props.width, item.props.height

def size_change(item, callback):
    """Connects the callback to the width, height property notifications.
    """
    item.set_data("w_sig_hdl", item.connect("notify::width", 
        size_change_cb, callback))
    item.set_data("h_sig_hdl", item.connect("notify::height", 
        size_change_cb, callback))

def unlink_size_change(item):
    item.disconnect(item.get_data("w_sig_hdl"))
    item.disconnect(item.get_data("h_sig_hdl"))

def set_size(item, size):
    """Sets the size of the item given size, a tuple of 
    (<width>, <height>)"""
    item.props.width, item.props.height = size

def top(item):
    return item.props.y

def bottom(item):
    return item.props.y + item.props.height

def left(item):
    return item.props.x

def right(item):
    return item.props.x + item.props.width

def top_right(item):
    return (right(item), top(item))

def bottom_right(item):
    return point_sum(pos(item), size(item))

def set_pos(item, pos):
    """Sets the position of item given pos, a tuple of (<x>, <y>)"""
    item.props.x, item.props.y = pos

def width(item):
    return item.props.width

def height(item):
    return item.props.height

def center(item):
    return point_sum(pos(item), point_mul(0.5, size(item)))

# these are callbacks for implementing "dragable object features
def drag_start(item, target, event, canvas, start_cb):
    """A callback which starts the drag operation of a dragable 
    object"""
    item.set_data("dragging", True)
    item.set_data("pendown", point_difference(pos(item), 
        event_coords(canvas, event)))
    if start_cb:
        start_cb(item)
    return True

def drag_end(item, target, event, end_cb):
    """A callback which ends the drag operation of a dragable object"""
    item.set_data("dragging", False)
    if end_cb:
        end_cb(item)
    return True

def translate_item_group(item, target, event, canvas, transform):
    """A callback which handles updating the position during a drag
    operation"""
    if item.get_data("dragging"):
        pos = point_sum(item.get_data("pendown"), event_coords(canvas, event))
        if transform:
            set_pos(item, transform(pos))
            return True
        set_pos(item, pos)
        return True
    return False

# callbacks for this feature are not implemented as nested 
# functions in order to minimize the potential memory impact this 
# might have when large numbers of dragable objects are present.

def make_dragable(canvas, item, transform=None, start=None, end=None):
    """Make item dragable with respect to the canvas. Call this 
    after make_selectable, or it will prevent the latter from working.
    """
    item.set_data("dragging", False)
    item.connect("button_press_event", drag_start, canvas, start)
    item.connect("button_release_event", drag_end, end)
    item.connect("motion_notify_event", translate_item_group, canvas,
        transform)

def group(*items):
    """Wrap all the canvas items in items in a smartgroup and return the
    resulting smartgroup. The item's current position is the offset
    within the smartgroup"""
    ret = smartgroup()
    
    for item in items:
        ret.add_child(item, pos(item))
    
    return ret

def make_item(factory):
    """Create a new goocanvas item given factory, a tuple of 
    * <class> - the class to create
    * <properties> - initial properties to set, such as color
    * <data> - initial data to set
    """
    klass, properties, data = factory
    ret = klass(**properties)
    for key, value in data.items():
        ret.set_data(key, value)
    return ret

def normalize_rect(mouse_down, cur_pos):
    """Given two points, representing the upper left and bottom right 
    corners of a rectangle (the order is irrelevant), return the tuple
    ((x,y), (width, height))"""
    w, h = point_difference(cur_pos, mouse_down)
    x, y = mouse_down

    if w < 0:
        w = abs(w)
        x -= w
    if h < 0:
        h = abs(h)
        y -= h

    return (x, y), (w, h)

def object_select_cb(item, target, event, canvas, changed_cb):
    prev = canvas.get_data("selected_objects")
    if item in prev:
        return
    if (event.state & gtk.gdk.SHIFT_MASK):
        prev.add(item)
        changed_cb(prev, set())
    else:
        selected = set()
        selected.add(item)
        canvas.set_data("selected_objects", selected)
        changed_cb(selected, prev)
    return False

def make_selectable(canvas, object):
    """Make the object selectable with respect to canvas. This means
    that the item will be included in the current selection, and that
    clicking the object will select it. Must be called before 
    make_dragable, as it will block the action of this handler"""
    object.set_data("selectable", True)
    object.connect("button_press_event", object_select_cb, canvas,
        canvas.get_data("selection_callback"))

def delete_from_selection(canvas, item):
    selected = canvas.get_data("selected_objects")
    set_selection(canvas, selected - set([item]))

def set_selection(canvas, new):
    prev = canvas.get_data("selected_objects")
    deselected = prev - new
    canvas.set_data("selected_objects", new)
    canvas.get_data("selection_callback")(new, deselected)

def manage_selection(canvas, marquee, overlap, changed_cb=None):
    """Keep track of the current selection in canvas, including
    * providing a rectangular selection marquee
    * tracking specific canvas objects
    Note: objects must be made selectable by calling make_selectable()
    on the object before they will be reported by any selection changes
    - overlap: True if you want items that merely intersect the 
        data field to be considered selected.
    - marquee: a goocanvas.Rectangle() to be used as the selection 
        marquee (really, any canvas item with x, y, width, height 
        properties). This object should not already be added to the
        canvas.
    - changed_cb: a callback with signature (selected, deselected)
      """

    def objects_under_marquee(event):
        pos, size = normalize_rect(mouse_down[0], event_coords(
            canvas, event))
        bounds = goocanvas.Bounds(*(pos + point_sum(pos, size)))
        selected = canvas.get_items_in_area(bounds, True, overlap, 
            containers)
        if selected:
            return set((found for found in selected if 
                found.get_data("selectable")))
        return set()

    def selection_start(item, target, event):
        root.add_child(marquee)
        cursor = event_coords(canvas, event)
        set_pos(marquee, cursor)
        selecting[0] = True
        mouse_down[0] = cursor
        set_pos(marquee, cursor) 
        set_size(marquee, (0, 0))
        return True

    def selection_end(item, target, event):
        selecting[0] = False
        marquee.remove()
        prev = canvas.get_data("selected_objects")
        selected = objects_under_marquee(event)
        canvas.set_data("selected_objects", selected)
        if changed_cb:
            changed_cb(selected, prev.difference(selected))
        return True

    def selection_drag(item, target, event):
        if selecting[0]:
            pos_, size_ = normalize_rect(mouse_down[0], 
                event_coords(canvas, event))
            set_size(marquee, size_)
            set_pos(marquee, pos_)
            return True
        return False

    canvas.set_data("selected_objects", set())
    canvas.set_data("selection_callback", changed_cb)
    containers = True
    selecting = [False]
    mouse_down = [None]
    root = canvas.get_root_item()
    root.connect("button_press_event", selection_start)
    root.connect("button_release_event", selection_end)
    root.connect("motion_notify_event", selection_drag)

