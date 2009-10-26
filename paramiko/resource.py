# Copyright (C) 2003-2007  Robey Pointer <robey@lag.net>
#
# This file is part of paramiko.
#
# Paramiko is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# Paramiko is distrubuted in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Paramiko; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA.

"""
Resource manager.
"""

import weakref


class ResourceManager (object):
    """
    A registry of objects and resources that should be closed when those
    objects are deleted.
    
    This is meant to be a safer alternative to python's C{__del__} method,
    which can cause reference cycles to never be collected.  Objects registered
    with the ResourceManager can be collected but still free resources when
    they die.
    
    Resources are registered using L{register}, and when an object is garbage
    collected, each registered resource is closed by having its C{close()}
    method called.  Multiple resources may be registered per object, but a
    resource will only be closed once, even if multiple objects register it.
    (The last object to register it wins.)
    """
    
    def __init__(self):
        self._table = {}
        
    def register(self, obj, resource):
        """
        Register a resource to be closed with an object is collected.
        
        When the given C{obj} is garbage-collected by the python interpreter,
        the C{resource} will be closed by having its C{close()} method called.
        Any exceptions are ignored.
        
        @param obj: the object to track
        @type obj: object
        @param resource: the resource to close when the object is collected
        @type resource: object
        """
        def callback(ref):
            try:
                resource.close()
            except:
                pass
            del self._table[id(resource)]

        # keep the weakref in a table so it sticks around long enough to get
        # its callback called. :)
        self._table[id(resource)] = weakref.ref(obj, callback)


# singleton
ResourceManager = ResourceManager()
