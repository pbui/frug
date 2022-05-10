#!/usr/bin/env python

#-------------------------------------------------------------------------------
# setup.py: frug setup
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

from distutils		import log
from distutils.command	import install_scripts
from distutils.core	import setup
from stat		import ST_MODE

#-------------------------------------------------------------------------------
# Classes
#-------------------------------------------------------------------------------

class	frug_install_scripts(install_scripts.install_scripts):
    def run(self):
	if not self.skip_build:                               
	    self.run_command('build_scripts')
	self.outfiles = self.copy_tree(self.build_dir, self.install_dir)
	if os.name == 'posix':
	    for file in self.get_outputs():
		if self.dry_run:
		    log.info("changing mode of %s", file)
		else:
		    mode = ((os.stat(file)[ST_MODE]) | 0555) & 07777
		    log.info("changing mode of %s to %o", file, mode)
		    os.chmod(file, mode)
		    # Basically the same but remove .py extension
		    file_new = '.'.join(file.split('.')[:-1])
		    os.rename(file, file_new)
		    log.info("renaming %s to %s", file, file_new)

#-------------------------------------------------------------------------------
# Configuration
#-------------------------------------------------------------------------------

setup(	name	     = 'frug',
	version	     = '0.3.3',
	description  = 'Simple mp3 player',
	author	     = 'Peter Bui',
	author_email = 'peter.j.bui@gmail.com',
	license	     = 'zlib',

	packages     = ['frug'],
	scripts	     = ['frug.py'],

	cmdclass     = { 'install_scripts' : frug_install_scripts }
     )

#-------------------------------------------------------------------------------
# vim: sts=4 sw=4 ts=8 ft=python
#-------------------------------------------------------------------------------
