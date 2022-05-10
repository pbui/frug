#!/usr/bin/env python

#-------------------------------------------------------------------------------
# widgets.py: simple mp3 player widgets
#-------------------------------------------------------------------------------

# Copyright (c) 2008 Peter Bui. All Rights Reserved.

# This software is provided 'as-is', without any express or implied warranty.
# In no event will the authors be held liable for any damages arising from the
# use of this software.

# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:

# 1. The origin of this software must not be misrepresented; you must not claim
# that you wrote the original software. If you use this software in a product,
# an acknowledgment in the product documentation would be appreciated but is
# not required.

# 2. Altered source versions must be plainly marked as such, and must not be
# misrepresented as being the original software.  

# 3. This notice may not be removed or altered from any source distribution.

# Peter Bui <peter.j.bui@gmail.com>

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import curses
import os
import random
import re
import sys

import carapace

from carapace.colormap	import ColorMap
from carapace.widget	import FileList, FileText, List, Text
from carapace.mixin	import NotebookMixIn, TabMixIn

from player		import Player

#-------------------------------------------------------------------------------
# Classes
#-------------------------------------------------------------------------------

class	BrowserTab(FileList, TabMixIn):

    def	__init__(self):
	FileList.__init__(self)
	TabMixIn.__init__(self, 0, 'Browse')

	self.color_pair = 0
	self.attribute = 0
	self.common_list = []
	self.enable_embolden = True
	self.select_history = {}
	self.highlight_mod = \
	    curses.color_pair(ColorMap['WHITE/BLUE']) | curses.A_BOLD
	self.embolden_mod = \
	    curses.color_pair(ColorMap['WHITE/BLACK']) | curses.A_BOLD

	self.pwd = os.path.realpath('.')

    #---------------------------------------------------------------------------

    def	change_directory(self, directory):
	scroll_index = self.scroll_index
	select_index = self.select_index

	if (scroll_index + select_index) > 0:
	    self.select_history[self.pwd] = (scroll_index, select_index)

	FileList.change_directory(self, directory)

	if self.select_history.has_key(self.pwd):
	    self.scroll_index, self.select_index = self.select_history[self.pwd]

	self.message = os.path.basename(self.pwd)
    
    #---------------------------------------------------------------------------
    
    def	draw(self, screen, row):
	self.embolden_list = []
	file_index = 1

	for f in sorted(os.listdir(self.pwd)):
	    f = os.path.abspath(f)
	    try:
		self.common_list.index(f)
		self.embolden_list.append(file_index)
	    except ValueError:
		pass
	    file_index += 1

	FileList.draw(self, screen, row)
    
    #---------------------------------------------------------------------------

    def	add_file(self, file):
	self.common_list.append(file)
    
    def	delete_file(self, file):
	try:
	    self.common_list.remove(file)
	except ValueError:
	    pass

#-------------------------------------------------------------------------------

class	PlaylistTab(List, Player, TabMixIn):

    def	__init__(self):
	List.__init__(self)
	Player.__init__(self)
	TabMixIn.__init__(self, 0, 'Playlist')
	
	self.color_pair	= 0
	self.attribute  = 0
	self.file_index = -1
	self.enable_embolden = True
	self.highlight_mod = \
	    curses.color_pair(ColorMap['WHITE/BLUE']) | curses.A_BOLD
	self.embolden_mod = \
	    curses.color_pair(ColorMap['WHITE/BLACK']) | curses.A_BOLD
    
    #---------------------------------------------------------------------------
    
    def shuffle(self):
	if self.file_index >= 0:
	    self.widgets[self.file_index].is_selected = True

	random.shuffle(self.widgets)
	
	for i, w in enumerate(self.widgets):
	    if hasattr(w, 'is_selected'):
		self.file_index = i
		delattr(w, 'is_selected')

    #---------------------------------------------------------------------------
   
    def	swap_widgets(self, widget1, widget2):
	widget1_index = self.get_widget_index(widget1)
	widget2_index = self.get_widget_index(widget2)

	if List.swap_widgets(self, widget1, widget2):
	    if widget1_index == self.file_index:
		self.file_index = widget2_index
	    elif widget2_index == self.file_index:
		self.file_index = widget1_index
    
    #---------------------------------------------------------------------------
    
    def	draw(self, screen, row):
	self.embolden_list = [self.file_index]
	List.draw(self, screen, row)
    
    #---------------------------------------------------------------------------

    def	add_file(self, file):
	self.add_widget(PlaylistText(file, self.color_pair, self.attribute))
    
    def	delete_file(self, file):
	adjusted_index = self.scroll_index + self.select_index

	if self.select_index < 0: return
	if adjusted_index == self.file_index: self.stop()
	if adjusted_index <= self.file_index: self.file_index -= 1

	self.delete_widget(self.widgets[adjusted_index])

	if len(self.widgets) == 0: 
	    self.select_index = -1
	elif adjusted_index >= len(self.widgets):
	    self.select_index -= 1
    
    #---------------------------------------------------------------------------
    
    def	previous_file(self):
	if (len(self.widgets) == 0 or self.file_index <= 0):
	    self.file_index = -1
	    self.set_state(Player.STOP_STATE)
	    return None
	else:
	    self.file_index -= 1
	    return (self.get_current_file())

    def	next_file(self):
	if (len(self.widgets) == 0 or self.file_index == len(self.widgets)):
	    self.file_index = -1
	    self.set_state(Player.STOP_STATE)
	    return None
	else:
	    self.file_index += 1
	    return (self.get_current_file())
    
    #---------------------------------------------------------------------------
    
    def	play_previous_file(self):
	self.play(self.previous_file())

    def	play_next_file(self):
	self.play(self.next_file())
    
    #---------------------------------------------------------------------------

    def	get_current_file(self):
	if (self.file_index < 0 or self.file_index == len(self.widgets)):
	    return None
	else:
	    return (self.widgets[self.file_index].get_value())
    
    #---------------------------------------------------------------------------

    def	clear_widgets(self):
	self.file_index = -1
	List.clear_widgets(self)

#-------------------------------------------------------------------------------

class	PlaylistText(Text):
    
    def	__init__(self, file_path, color_pair=0, attribute=0):
	Text.__init__(self, file_path, color_pair, attribute)
	self.file_reg_ex = re.compile('.*\/(.*)\/(.*)\/[0-9]*[\s]+(.*)\..*')
	self.file_path	 = file_path

    def	draw(self, screen, row):
	m = self.file_reg_ex.search(self.file_path)
	if (m):
	    self.value = m.groups()[0] + ' - ' + m.groups()[2]
	else:
	    self.value = os.path.basename(self.file_path)
	Text.draw(self, screen, row)
	self.value = self.file_path

#-------------------------------------------------------------------------------

class	TitleBar(Text):

    def	__init__(self, current_tab, volume=0, color_pair=0, attribute=0):
	Text.__init__(self, '', color_pair, attribute)

	self.current_tab = current_tab
	self.volume = volume

    def	draw(self, screen, row):
	title_text  = self.current_tab.get_title()
	volume_text = "volume: %02d%%" % self.volume
	self.value  = title_text.ljust(curses.COLS - len(volume_text), ' ')
	self.value += volume_text
	Text.draw(self, screen, row)

    def set_current_tab(self, tab):
	self.current_tab = tab

    def	set_volume(self, volume):
	self.volume = volume

#-------------------------------------------------------------------------------
# vim: sts=4 sw=4 ts=8 ft=python
#-------------------------------------------------------------------------------
