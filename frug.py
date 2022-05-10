#!/usr/bin/env python

#-------------------------------------------------------------------------------
# frug.py: simple mp3 player
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
import re
import sys
import time

import carapace
import carapace.keys as keys

from carapace.colormap import ColorMap
from carapace.event import KeyboardGenerator, TimerGenerator
from carapace.mixin import NotebookMixIn
from carapace.shell import Shell
from carapace.widget import EditText, FileText, List, ProgressBar, Seperator, Text

from frug.widget import BrowserTab, PlaylistTab, TitleBar

#-------------------------------------------------------------------------------
# Class
#-------------------------------------------------------------------------------
  
class	Frug(Shell, NotebookMixIn):

    def	__init__(self):
	Shell.__init__(self)
	NotebookMixIn.__init__(self)

	# Make widgets
	self.title_bar = TitleBar(None, 0, ColorMap['YELLOW/BLACK'])
	self.seperator = Seperator()
	
	self.browse_tab	  = BrowserTab()
	self.playlist_tab = PlaylistTab()

	self.progress_bar = ProgressBar(use_percent=False)

	self.status_text = Text(' ', ColorMap['YELLOW/BLACK'])
	self.edit_text   = EditText('Search: ', ColorMap['YELLOW/BLACK'])

	# Add tabs and widgets
	self.add_tabs([self.browse_tab, self.playlist_tab])
	
	self.add_widget(self.title_bar) # 0
	self.add_widget(self.seperator) # 1
	self.add_widget(self.get_current_tab()) # 2
	self.add_widget(self.progress_bar) # 3
	self.add_widget(self.status_text)  # 4

	# Add generators/handlers
	self.kbd_gen = KeyboardGenerator()
	self.add_event_generator(self.kbd_gen)
	self.kbd_gen.get_mode('cmd').append_keymap({
	    ord('1')	    : 'switch-to-browse-tab',
	    ord('2')	    : 'switch-to-playlist-tab',
	    keys.KEY_TAB    : 'rotate-to-next-tab',
	    ord('c')	    : 'clear-list',
	    ord('d')	    : 'delete-list-item',
	    keys.KEY_SPACE  : 'select-list-item',
	    ord('K')	    : 'move-selected-item-up',
	    ord('J')	    : 'move-selected-item-down',
	    ord('N')	    : 'search-prev',
	    ord('n')	    : 'search-next',
	    ord('<')	    : 'play-previous',
	    ord('>')	    : 'play-next',
	    keys.KEY_CTRL_L : 'refresh-screen',
	    ord('-')	    : 'volume-down',
	    ord('+')	    : 'volume-up',
	    ord('p')	    : 'toggle-pause',
	    ord('s')	    : 'stop',
	    ord('z')	    : 'shuffle',
	    ord('/')	    : 'toggle-mode',
	})

	self.kbd_gen.auto_register_handlers(self, 'cmd')
	self.kbd_gen.auto_register_handlers(self, 'edt')
	
	self.add_event_generator(TimerGenerator('vol-timer-event', 1.0))
	self.add_event_handler('vol-timer-event', lambda shell, event, data: \
	    self.title_bar.set_volume(self.playlist_tab.get_volume()))

	# Setup widgets
	self.set_tab_widget_index(2)
	
	self.browse_tab.change_directory(os.path.realpath('.'))
	self.title_bar.set_current_tab(self.get_current_tab())
	self.title_bar.set_volume(self.playlist_tab.get_volume())

	self.draw_widgets()
    
    #---------------------------------------------------------------------------
   
    # Command mode handlers
   
    def cmd_select_down(self, shell, event, data):
	self.get_current_tab().select_down()
    
    def cmd_select_up(self, shell, event, data):
	self.get_current_tab().select_up()
    
    def cmd_select_page_down(self, shell, event, data):
	self.get_current_tab().select_page_down()
    
    def cmd_select_page_up(self, shell, event, data):
	self.get_current_tab().select_page_up()
    
    def cmd_enter(self, shell, event, data):
	browse_tab	= self.browse_tab
	playlist_tab	= self.playlist_tab
	selected_widget = self.get_current_tab().get_selected_widget()

	if selected_widget is None: return

	value = selected_widget.value
	if self.current_tab_id == browse_tab.id:
	    if os.path.isdir(value) or os.path.islink(value):
		browse_tab.change_directory(value)
	    else:
		self.add_file(value)
		self.play_file(value, len(playlist_tab.widgets) - 1)
	elif self.current_tab_id == playlist_tab.id:
	    file_index = playlist_tab.scroll_index + playlist_tab.select_index
	    self.play_file(value, file_index)

    def cmd_clear_list(self, shell, event, data):
	self.browse_tab.common_list = []
	self.playlist_tab.stop()
	self.playlist_tab.clear_widgets()
	self.status_text.set_value('Cleared Playlist')
    
    def cmd_delete_list_item(self, shell, event, data):
	selected_widget = self.get_current_tab().get_selected_widget()
	
	if selected_widget is None: return

	value = selected_widget.value
	if self.current_tab_id == self.playlist_tab.id:
	    self.browse_tab.delete_file(value)
	    self.playlist_tab.delete_file(value)
    
    def cmd_select_list_item(self, shell, event, data):
	selected_widget = self.get_current_tab().get_selected_widget()
	
	if selected_widget is None: return
	
	value = selected_widget.value
	if self.current_tab_id == self.browse_tab.id:
	    if os.path.isfile(value):
		self.add_file(value)
	    elif os.path.isdir(value):
		self.add_directory(value)

    def cmd_move_selected_item_up(self, shell, event, data):
	playlist_tab = self.playlist_tab
	if self.current_tab_id == playlist_tab.id:
	    selected_widget_index = playlist_tab.get_selected_widget_index()

	    playlist_tab.move_widget_up(selected_widget_index)
	    playlist_tab.select_up()
    
    def cmd_move_selected_item_down(self, shell, event, data):
	playlist_tab = self.playlist_tab
	if self.current_tab_id == playlist_tab.id:
	    selected_widget_index = playlist_tab.get_selected_widget_index()

	    playlist_tab.move_widget_down(selected_widget_index)
	    playlist_tab.select_down()
    
    def cmd_search_prev(self, shell, event, data):
	self.get_current_tab().search_prev(self.edit_text.value)
    
    def cmd_search_next(self, shell, event, data):
	self.get_current_tab().search_next(self.edit_text.value)

    def cmd_switch_to_browse_tab(self, shell, event, data):
	self.switch_to_tab(self.browse_tab.id)
	self.title_bar.set_current_tab(self.get_current_tab())
    
    def cmd_switch_to_playlist_tab(self, shell, event, data):
	self.switch_to_tab(self.playlist_tab.id)
	self.title_bar.set_current_tab(self.get_current_tab())
	    
    def cmd_rotate_to_next_tab(self, shell, event, data):
	self.rotate_to_next_tab()
	self.title_bar.set_current_tab(self.get_current_tab())
    
    def cmd_play_previous(self, shell, event, data):
	self.playlist_tab.stop()
	self.playlist_tab.play_previous_file()

    def cmd_play_next(self, shell, event, data):
	self.playlist_tab.stop()
	self.playlist_tab.play_next_file()
    
    def cmd_toggle_pause(self, shell, event, data):
	self.playlist_tab.play()
	
    def cmd_stop(self, shell, event, data):
	self.playlist_tab.stop()
    
    def cmd_shuffle(self, shell, event, data):
	if self.current_tab_id == self.playlist_tab.id:
	    self.playlist_tab.shuffle()
    
    def cmd_volume_down(self, shell, event, data):
	self.title_bar.set_volume(self.playlist_tab.set_volume_down())
    
    def cmd_volume_up(self, shell, event, data):
	self.title_bar.set_volume(self.playlist_tab.set_volume_up())
	   
    def cmd_refresh_screen(self, shell, event, data):
	self.refresh_widgets()

    def cmd_toggle_mode(self, shell, event, data):
	self.widgets[4] = self.edit_text
	self.edit_text.clear_buffer()
	self.kbd_gen.set_mode('edt')

    def cmd_quit(self, shell, event, data):
	self.playlist_tab.stop()
	self.exit(0)
    
    #---------------------------------------------------------------------------

    # Editor methods
    
    def edt_any_key_press(self, shell, event, data):
	if re.compile('[-_./a-zA-Z0-9]').match(curses.keyname(data)):
	    self.edit_text.buffer += curses.keyname(data)
	    self.set_refresh_screen(True)

    def edt_backspace(self, shell, event, data):
	self.edit_text.buffer = self.edit_text.buffer[:-1]
	
    def edt_enter(self, shell, event, data):
	self.get_current_tab().search_next(self.edit_text.value)
	self.edt_toggle_mode(shell, event, data)

    def edt_toggle_mode(self, shell, event, data):
	self.widgets[4] = self.status_text
	self.kbd_gen.set_mode('cmd')
    
    #---------------------------------------------------------------------------

    # Add methods
   
    def	add_file(self, file):
	if os.path.exists(file) and file.lower().endswith('mp3'):
	    self.browse_tab.add_file(file)
	    self.playlist_tab.add_file(file)
	    self.status_text.set_value('Added: ' + os.path.basename(file))
    
    def	add_directory(self, directory):
	for dir_path, dir_names, file_names in os.walk(directory):
	    for f in sorted(file_names):
		self.add_file(os.path.join(dir_path, f))
	
	self.status_text.set_value('Added: ' + directory)

    #---------------------------------------------------------------------------
   
    def	play_file(self, file, file_index):
	if file_index < 0: return

	self.playlist_tab.stop()
	self.playlist_tab.play(file)
	self.playlist_tab.file_index = file_index
	self.progress_bar.set_time_length(self.playlist_tab.get_time_length())
    
    #---------------------------------------------------------------------------

    def	run(self):
	playlist_tab = self.playlist_tab
	progress_bar = self.progress_bar
	status_text  = self.status_text

	while True:
	    # If there is song in queue and we are idle, then play it
	    if playlist_tab.is_idle():
		progress_bar.set_time_pos(0)
		progress_bar.set_time_length(0)
		playlist_tab.play_next_file()
		progress_bar.set_time_length(playlist_tab.get_time_length())
		continue
	    else:
		cfile = playlist_tab.get_current_file()
		if cfile:
		    cfile = os.path.basename(cfile)
		    if playlist_tab.is_paused():
			status_text.set_value('Paused: ' + cfile)
			progress_bar.set_time_pos(playlist_tab.get_time_pos())
		    elif self.playlist_tab.is_playing():
			status_text.set_value('Playing: ' + cfile)
			progress_bar.set_time_pos(playlist_tab.get_time_pos())
		    else:
			status_text.set_value('Stopped: ' + cfile)
			progress_bar.set_time_pos(0)
		else:
		    progress_bar.set_time_pos(0)
		    progress_bar.set_time_length(0)
		    status_text.set_value('Stopped')

		self.set_refresh_screen(True)

	    self.do_one_loop()

#-------------------------------------------------------------------------------
# Main Execution
#-------------------------------------------------------------------------------

if __name__ == '__main__':
    f = Frug()
    f.run()

#-------------------------------------------------------------------------------
# vim: sts=4 sw=4 ts=8 ft=python
#-------------------------------------------------------------------------------
