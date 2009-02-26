import gtk
import gst
import gobject

target = [
    ('GST_ELEMENT', 0, 0)
]

class Browser(gtk.ScrolledWindow):

    def __init__(self):
        gtk.ScrolledWindow.__init__(self)
        self.__createUi()

    def get_data(w, context, s_d, info, time):
        s_d.set(s_d.target, 8, treemodel[row][1])

    def __createUi(self):

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
        self.add(treeview)

