# coding: utf-8
"""
Abstraction code for shell elements.
"""
from gi.repository import Gtk, Gdk, GdkX11, GObject
from ewmh import EWMH
import Xlib

class SurfaceType:
	"""Enum for surface types."""
	DEFAULT = 0
	DOCK = 1
	OVERLAY = 2
	NOTIFICATION = 3
	LAUNCHER = 4

def x11_atom_for_type(ewmh, type):
	"""Gets the atom int for a specific surface type."""
	if type == SurfaceType.DEFAULT:
		ewmh_type = '_NET_WM_WINDOW_TYPE_NORMAL'
	elif type == SurfaceType.DOCK:
		ewmh_type = '_NET_WM_WINDOW_TYPE_DOCK'
	elif type == SurfaceType.OVERLAY:
		ewmh_type = '_NET_WM_WINDOW_TYPE_DIALOG'
	elif type == SurfaceType.NOTIFICATION:
		ewmh_type = '_NET_WM_WINDOW_TYPE_NOTIFICATION'
	elif type == SurfaceType.LAUNCHER:
		ewmh_type = '_NET_WM_WINDOW_TYPE_DESKTOP'
	else:
		raise ValueError("incorrect type")
	return ewmh.display.intern_atom(ewmh_type)

class Surface(Gtk.Window):
	"""
	Generic class for shell elements.
	"""
	__gtype_name__ = 'ShellSurface'

	# Currently this is derived from Gtk.Window; the final goal is to have
	# something akin to Phosh's PhoshLayerSurface, but with support for
	# both X11 and Wayland, hopefully with as little breakage during the
	# transition as possible.

	def __init__(self, application,
			valign=Gtk.Align.START, halign=Gtk.Align.END,
			vexpand=False, hexpand=False, width=0, height=0,
			visible=True, top=0, type=SurfaceType.DEFAULT):
		"""Initializes a shell surface."""
		super().__init__(
			application=application,
			resizable=False,
			decorated=False,
			deletable=False,
			visible=visible
		)

		self._hexpand = hexpand
		self._vexpand = vexpand

		# Set surface width/height
		monitor = Gdk.Display.get_default().get_monitors()[0]
		self._monitor_width = monitor.get_geometry().width
		self._monitor_height = monitor.get_geometry().height

		self.notify('monitor-width')
		self.notify('monitor-height')

		monitor.connect('notify::geometry', self.update_size)

		if hexpand is True:
			width = self._monitor_width
		if vexpand is True:
			height = self._monitor_height - top
		self.set_size_request(width, height)

		self.width = width
		self.height = height

		# Set surface info and alignment
		try:
			EWMH().getActiveWindow()
		except: # noqa: E722
			pass # No x11/ewmh support
		else:
			# We need to show the window temporarily to get the X11 window
			self.show()
			self.unmap()

			ewmh = EWMH()
			x11_display = ewmh.display
			x11_window_id = GdkX11.X11Surface.get_xid(self.get_surface())
			x11_window = x11_display.create_resource_object('window', x11_window_id)

			# herbstluftwm only listens to properties when a window is mapped;
			# However, as we need to show the window to get the X11 ID from the
			# resulting surface, and closing it closes the program (???),
			# we need to manually unmap the window here (we re-map it at the
			# end).
			unmap_event = Xlib.protocol.event.UnmapNotify(
				event=x11_window,
				window=x11_window,
				from_configure=False
			)
			x11_window.send_event(unmap_event)

			# Set strut for dock
			if type == SurfaceType.DOCK:
				x11_window.change_property(
					x11_display.intern_atom('_NET_WM_STRUT'),
					x11_display.intern_atom('CARDINAL'),
					32, [0, 0, height, 0]
				)

			ewmh.setWmState(x11_window, 2, '_NET_WM_STATE_SKIP_TASKBAR')

			# Set window type
			x11_window.change_property(
				x11_display.intern_atom('_NET_WM_WINDOW_TYPE'),
				x11_display.intern_atom('ATOM'),
				32, [
					x11_atom_for_type(ewmh, type),
					x11_display.intern_atom('_NET_WM_WINDOW_TYPE_NORMAL')
				]
			)

			# Re-map window; see earlier comment
			remap_event = Xlib.protocol.event.MapNotify(
				event=x11_window,
				window=x11_window,
				override=False
			)
			x11_window.send_event(remap_event)
			self.map()

			x11_window.get_property(x11_display.intern_atom('_NET_WM_WINDOW_TYPE'), x11_display.intern_atom('ATOM'), 0, 32)

		if not visible:
			self.set_visible(False)

	def update_size(self):
		"""Updates the size request of the surface based on its variables."""
		self.notify('surface-width')
		self.notify('surface-height')

		monitor = Gdk.Display.get_default().get_monitor_at_surface(
			self.get_surface()
		)
		self._monitor_width = monitor.get_geometry().width
		self._monitor_height = monitor.get_geometry().height

		if self.hexpand is True:
			self.width = self._monitor_width
		if self.vexpand is True:
			self.height = self._monitor_height

		self.set_size_request(self.width, self.height)

	@GObject.Property(type=int, flags=GObject.ParamFlags.READABLE)
	def surface_width(self):
		"""
		Width of the surface.

		Should be used in derived objects instead of the monitor width, as
		this allows it to be easily changed for debugging purposes.
		"""
		return self.width

	def set_width(self, value):
		"""Sets the width of the surface."""
		self.width = value
		self.update_size()

	@GObject.Property(type=int, flags=GObject.ParamFlags.READABLE)
	def surface_height(self):
		"""
		Height of the surface.

		Should be used in derived objects instead of the monitor height, as
		this allows it to be easily changed for debugging purposes.
		"""
		return self.height

	def set_height(self, value):
		"""Sets the height of the surface."""
		self.height = value
		self.update_size()

	@GObject.Property(type=int, flags=GObject.ParamFlags.READABLE)
	def monitor_width(self):
		"""
		Width of the monitor.
		"""
		return self._monitor_width

	@GObject.Property(type=int, flags=GObject.ParamFlags.READABLE)
	def monitor_height(self):
		"""
		Height of the monitor.
		"""
		return self._monitor_height

	@GObject.Property(type=bool, default=False)
	def hexpand(self):
		"""
		Whether to expand the surface horizontally.
		"""
		return self._hexpand

	@hexpand.setter
	def set_hexpand(self, value):
		"""
		Changes whether to expand the surface horizontally.
		"""
		self._hexpand = value

	@GObject.Property(type=bool, default=False)
	def vexpand(self):
		"""
		Whether to expand the surface vertically.
		"""
		return self._vexpand

	@vexpand.setter
	def set_vexpand(self, value):
		"""
		Changes whether to expand the surface vertically.
		"""
		self._vexpand = value
