# coding: utf-8
"""
Handles configuration for the Aspinwall launcher
"""
from gi.repository import Gio

config = Gio.Settings.new('org.dithernet.aspinwall.launcher')
bg_config = Gio.Settings.new('org.gnome.desktop.background')
