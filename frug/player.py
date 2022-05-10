#!/usr/bin/env python

#-------------------------------------------------------------------------------
# player.py: simple mp3 player widgets
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

import os
import re
import signal
import subprocess
import sys

#-------------------------------------------------------------------------------
# Classes
#-------------------------------------------------------------------------------

class	Player():
    STOP_STATE	= 0
    IDLE_STATE	= 1
    PLAY_STATE	= 2
    PAUSE_STATE	= 3
    SEEK_STATE	= 4

    def	__init__(self):
	self.am_cmd = 'amixer set Master'
	self.id_cmd = 'id3v2 -l'
	self.mi_cmd = "mp3info -p '%S\\n'"
	self.mp_cmd = 'mplayer -quiet -slave'
	self.mp_process	= None

	self.state = Player.STOP_STATE
	
	self.percent_pos = 0
	self.time_length = 0
	self.time_pos	 = 0

	self.volume_reg_ex = re.compile('.*Playback.*\[([0-9]*)%].*')
	self.volume = 50
	self.get_volume()

    def	__del__(self):
	self.stop()
    
    def get_volume(self, args='0+'):
	try:
	    for line in os.popen(self.am_cmd + ' ' + args).readlines():
		m = self.volume_reg_ex.search(line)
		if (m):
		    self.volume = int(m.groups()[0])
		    break
	except IOError:
	    pass
	return (self.volume)

    def set_volume_up(self):
	return (self.get_volume('1%+'))
   
    def set_volume_down(self):
	return (self.get_volume('1%-'))

    def	get_time_length(self):
	return (self.time_length)
    
    def	get_time_pos(self):
	if (not(self.is_idle() or self.is_paused() or self.is_stopped())):
	    xprint(self.mp_process.stdin, 'get_time_pos')
	    try:
		time_pos = self.mp_process.stdout.readline().split('=')[1]
		self.time_pos = float(time_pos)
	    except IndexError, IOError:
		pass
	return (self.time_pos)

    def	get_percent_pos(self):
	if (not(self.is_idle() or self.is_paused() or self.is_stopped())):
	    xprint(self.mp_process.stdin, 'get_percent_pos')
	    try:
		percent_pos = self.mp_process.stdout.readline().split('=')[1]
		self.percent_pos = float(percent_pos)
	    except IndexError, IOError:
		pass
	return (self.percent_pos)

    def	play(self, filename=None):
	if (self.state == Player.STOP_STATE or
	    self.state == Player.IDLE_STATE):
	    if (filename):
		self.mp_process = subprocess.Popen(
		    self.mp_cmd + ' "' + filename + '"', 
		    shell=True, 
		    stderr=subprocess.PIPE,
		    stdin=subprocess.PIPE,
		    stdout=subprocess.PIPE)

		self.current_file = filename
		self.state = Player.PLAY_STATE

		self.percent_pos = 0
		self.time_pos    = 0

		id_cmd = self.id_cmd + ' "' + filename + '" | grep TLEN'
		mi_cmd = self.mi_cmd + ' "' + filename + '"'

		try:
		    tl = os.popen(id_cmd).readline()

		    if len(tl):
			self.time_length = int(tl.split(' ')[2]) / 1000
		    else:
			self.time_length = int(os.popen(mi_cmd).readline())
		except IOError:
		    pass

		while True:
		    line = self.mp_process.stdout.readline()
		    if (line.startswith('Starting')): break

	elif (self.state == Player.PLAY_STATE):
	    xprint(self.mp_process.stdin, 'pause')
	    self.state = Player.PAUSE_STATE
	
	elif (self.state == Player.PAUSE_STATE):
	    xprint(self.mp_process.stdin, 'pause')
	    self.state = Player.PLAY_STATE

    def	stop(self):
	if (self.mp_process):
	    xprint(self.mp_process.stdin, 'quit')
	self.mp_process	= None
	self.state = Player.STOP_STATE

	self.percent_pos = 0
	self.time_pos	 = 0

    def	is_idle(self):
	if (self.state == Player.PLAY_STATE):
	    if (self.mp_process.poll() is not(None)):
		self.mp_process	= None
		self.state = Player.IDLE_STATE

		self.percent_pos = 0
		self.time_pos	 = 0
	return (self.state == Player.IDLE_STATE)
    
    def	is_paused(self):
	return (self.state == Player.PAUSE_STATE)
    
    def	is_playing(self):
	return (self.state == Player.PLAY_STATE)
    
    def	is_stopped(self):
	return (self.state == Player.STOP_STATE)

    def	get_state(self):
	return (self.state)
    
    def	set_state(self, state):
	self.state = state

#-------------------------------------------------------------------------------
# Functions
#-------------------------------------------------------------------------------

def xprint(stream, output_item):
    try:
	print >>stream, output_item
    except IOError:                                           
	pass

#-------------------------------------------------------------------------------
# vim: sts=4 sw=4 ts=8 ft=python
#-------------------------------------------------------------------------------
