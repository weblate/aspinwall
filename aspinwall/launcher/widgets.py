# coding: utf-8
"""
Contains basic code for the launcher's widget handling.
"""
from gi.repository import Gtk, Gdk, GObject
import os

@Gtk.Template(filename=os.path.join(os.path.dirname(__file__), 'ui', 'widgetheader.ui'))
class AspWidgetHeader(Gtk.Box):
	"""Header for AspWidget."""
	__gtype_name__ = 'AspWidgetHeader'

	icon = Gtk.Template.Child('widget_header_icon')
	title = Gtk.Template.Child('widget_header_title')

	def __init__(self, widget, aspwidget):
		"""Initializes an AspWidgetHeader."""
		super().__init__()
		self._widget = widget
		self._aspwidget = aspwidget

		self.icon.set_from_icon_name(self._widget.icon)
		self.title.set_label(self._widget.title)

		self.add_controller(self._aspwidget.drag_source)

	@Gtk.Template.Callback()
	def remove(self, *args):
		"""Removes the parent AspWidget."""
		self._aspwidget.remove()

class AspWidget(Gtk.Box):
	"""
	Box containing a widget, alongside with its header.

	This class is used to display widgets, and uses the Widget class as
	the widget content.

	For information on creating widgets, see docs/widgets/creating-widgets.md.
	"""
	__gtype_name__ = 'AspWidget'

	def __init__(self, widget_class, widgetbox, config={}):
		"""Initializes a widget display."""
		# Inheriting from objects created with templates isn't possible, so
		# we create the object manually.
		super().__init__(orientation=Gtk.Orientation.VERTICAL)
		self.add_css_class('aspinwall-widget-wrapper')

		self._widget = widget_class(config)
		self._widgetbox = widgetbox

		# Set up drag source
		self.drag_source = Gtk.DragSource(actions=Gdk.DragAction.MOVE)
		self.drag_source.connect("prepare", self.drag_prepare)
		self.drag_source.connect("drag-begin", self.drag_begin)
		self.drag_source.connect("drag-end", self.drag_end)
		# End drag source setup

		# Set up drop target
		self.drop_target = Gtk.DropTarget(actions=Gdk.DragAction.MOVE)
		self.drop_target.set_gtypes([GObject.TYPE_INT])
		self.add_controller(self.drop_target)

		self.drop_target.connect('drop', self.on_drop)
		self.drop_target.connect('enter', self.on_enter)
		self.drop_target.connect('leave', self.on_leave)
		# End drop target setup

		# Set up widget content
		self.container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.END, hexpand=True)

		self.widget_header = AspWidgetHeader(self._widget, self)
		self.container.append(self.widget_header)

		self.widget_content = self._widget
		self.widget_content.add_css_class('aspinwall-widget-content')
		self.container.append(self.widget_content)

		self.append(self.container)

		# Set up widget "margins"
		self.w_margin_top = AspWidgetMargin('top', self)
		self.prepend(self.w_margin_top)
		self.w_margin_bottom = AspWidgetMargin('bottom', self)
		self.append(self.w_margin_bottom)

		self.container.add_css_class('aspinwall-widget')

	def __str__(self):
		return self._widget.num

	def remove(self):
		"""Removes the widget from its parent WidgetBox."""
		self._widgetbox.remove_widget(self)

	def drag_prepare(self, *args):
		"""Returns the GdkContentProvider for the drag operation"""
		return Gdk.ContentProvider.new_for_value(
			self._widgetbox.get_widget_position(self)
		)

	def drag_begin(self, drag_source, *args):
		"""Operations to perform when the drag operation starts."""
		drag_source.set_icon(Gtk.WidgetPaintable(widget=self), self.get_allocation().width / 2, 10)
		self.add_css_class('dragged')

	def drag_end(self, *args):
		"""Operations to perform when the drag operation ends."""
		self.remove_css_class('dragged')

	def on_drop(self, stub, target, x, y):
		"""
		Performs the widget move when a dragged widget dropped.

		Note that this is performed from the perspective of the drag target;
		thus, self in this context is the widget which the dragged widget was
		dropped onto.
		"""
		current_pos = self._widgetbox.get_widget_position(self)
		if target > current_pos:
			self._widgetbox.move_widget(target, current_pos)
		else:
			self._widgetbox.move_widget(target, current_pos + 1)
		self.remove_css_class('on-enter')

	def on_enter(self, *args):
		self.add_css_class('on-enter')
		return 0

	def on_leave(self, *args):
		self.remove_css_class('on-enter')
		return 0

class AspWidgetMargin(Gtk.Box):
	"""Margin that lights up when a widget is dragged on top"""

	def __init__(self, attachment, widget):
		"""Initializes the AspWidgetMargin"""
		super().__init__(height_request=7)
		self.attachment = attachment
		self._widget = widget
