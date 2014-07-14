#!/usr/bin/env python
###############################################################################
#                                                                             #
#    manifestManager.py                                                       #
#                                                                             #
#    Work with online data manifests (creating / syncing / validating)        #
#                                                                             #
#    Copyright (C) Michael Imelfort                                           #
#                                                                             #
###############################################################################
#                                                                             #
#    This program is free software: you can redistribute it and/or modify     #
#    it under the terms of the GNU General Public License as published by     #
#    the Free Software Foundation, either version 3 of the License, or        #
#    (at your option) any later version.                                      #
#                                                                             #
#    This program is distributed in the hope that it will be useful,          #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of           #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
#    GNU General Public License for more details.                             #
#                                                                             #
#    You should have received a copy of the GNU General Public License        #
#    along with this program. If not, see <http://www.gnu.org/licenses/>.     #
#                                                                             #
###############################################################################

__author__ = "Michael Imelfort"
__copyright__ = "Copyright 2014"
__credits__ = ["Michael Imelfort"]
__license__ = "GPLv3"
__version__ = "0.1.0"
__maintainer__ = "Michael Imelfort"
__email__ = "mike@mikeimelfort.com"
__status__ = "Dev"

###############################################################################
###############################################################################
###############################################################################
###############################################################################

__MANIFEST__ = ".dmanifest"

###############################################################################
###############################################################################
###############################################################################
###############################################################################

# system includes
import sys
import os
import hashlib

# local includes
from screamingbackpack.fileEntity import FileEntity as FE

###############################################################################
###############################################################################
###############################################################################
###############################################################################

class ManifestManager(object):
    """Use this interface for storing and managing file and paths"""
    def __init__(self):
        self.files = []

    def createManifest(self, path, manifestName=None):
        """inventory all files in path and create a manifest file"""
        if manifestName is None:
            manifestName = __MANIFEST__
        # make the root file entity
        root_path = os.path.abspath(path)
        root_fe = FE("d", 'root', ".", None, "-")
        self.files.append(root_fe)
        # now make all the ones below
        parents = [root_fe]
        dirs, files = self.listdir(path)[:2]
        self.walk(parents, root_path, '', dirs, files, skipFile=manifestName)

        with open(os.path.join(path, manifestName), 'w') as man_fh:
            for file in self.files:
                if file.parent is not None:
                    man_fh.write("%s\n" % file)


#-----------------------------------------------------------------------------
# Get the remote manifest file and check for differences

    def diffRemoteManifest(self,
                           manifestPath,
                           remoteUrl,
                           localManifestName=__MANIFEST__,
                           remoteManifestName=__MANIFEST__):
        """get the manifest file from the remote server and
        check for any differences from the local manifest

        returns a list of files that need to be updated
        """
        pass



#-----------------------------------------------------------------------------
# FS utilities

    def walk(self, parents, full_path, rel_path, dirs, files, skipFile=__MANIFEST__):
        """recursive walk through directory tree"""
        # first do files here
        for file in files:
            if file != skipFile:
                self.files.append(FE("f",
                                     file,
                                     rel_path,
                                     parents[-1],
                                     self.hashfile(os.path.join(full_path, file))
                                     )
                                  )
        for dir in dirs:
            # the walk will go into these dirs first
            tmp_fe = FE("d", dir, rel_path, parents[-1], "-")
            self.files.append(tmp_fe)
            parents.append(tmp_fe)
            new_full_path = os.path.join(full_path, dir)
            new_rel_path = os.path.join(rel_path, dir)
            new_dirs, new_files = self.listdir(new_full_path)[:2]
            self.walk(parents, new_full_path, new_rel_path, new_dirs, new_files)
            parents.pop()

    def listdir(self, path):
        """List dirs, files etc in path (one dir deep)"""
        dirs, files, links = [], [], []
        for name in os.listdir(path):
            path_name = os.path.join(path, name)
            if os.path.isdir(path_name):
                dirs.append(name)
            elif os.path.isfile(path_name):
                files.append(name)
            elif os.path.islink(path_name):
                links.append(name)
        return dirs, files, links

    def hashfile(self, fileName, blocksize=65536):
        """Hash a file and return the digest"""
        hasher = hashlib.sha256()
        with open(fileName) as fh:
            buf = fh.read(blocksize)
            while len(buf) > 0:
                hasher.update(buf)
                buf = fh.read(blocksize)
            return hasher.hexdigest()
        return "?"

###############################################################################
###############################################################################
###############################################################################
###############################################################################
