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
__version__ = "0.2.0"
__maintainer__ = "Michael Imelfort"
__email__ = "mike@mikeimelfort.com"
__status__ = "Beta"

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
import urllib2
import urllib
import shutil

# local includes
from screamingbackpack.fileEntity import FileEntity as FE

###############################################################################
###############################################################################
###############################################################################
###############################################################################

class ManifestManager(object):
    """Use this interface for storing and managing file and paths"""
    def __init__(self, manType=None):
        self.files = []
        if manType is not None:
            self.type = manType
        else:
            self.type = "generic"

    def createManifest(self, path, manifestName=None):
        """inventory all files in path and create a manifest file"""
        if manifestName is None:
            manifestName = __MANIFEST__
        # make the root file entity
        root_path = os.path.abspath(path)
        root_fe = FE('root', ".", None, "-", 0)
        self.files.append(root_fe)
        # now make all the ones below
        parents = [root_fe]
        dirs, files = self.listdir(path)[:2]
        self.walk(parents, root_path, '', dirs, files, skipFile=manifestName)

        with open(os.path.join(path, manifestName), 'w') as man_fh:
            # print the header
            man_fh.write("##%s##\tData manifest created by ScreamingBackpack version %s\n" % (self.type, __version__))
            for file in self.files:
                if file.parent is not None:
                    man_fh.write("%s\n" % file)

    def diffManifests(self,
                      localManifestLocation,
                      sourceManifestLocation,
                      localManifestName=None,
                      sourceManifestName=None,
                      printDiffs=False):
        """check for any differences between two manifests

        if remote is true then sourceManifestLocation is a URL
        returns a list of files that need to be updated
        """
        if localManifestName is None:
            localManifestName = __MANIFEST__
        if sourceManifestName is None:
            sourceManifestName = __MANIFEST__

        # get the "type" of the local manifest
        l_type = "generic"
        with open(os.path.join(localManifestLocation, localManifestName)) as l_man:
            for line in l_man:
                if line[0] == "#":
                    l_type = self.getManType(line)
                break

        # load the source manifest
        s_type = "generic"
        source_man = {}
        source = ""
        # first we assume it is remote
        try:
            s_man = urllib2.urlopen(sourceManifestLocation + "/" + sourceManifestName)
            source = sourceManifestLocation + "/"
        except ValueError:
            # then it is probably a file
            s_man = open(os.path.join(sourceManifestLocation, sourceManifestName))
            source = os.path.join(sourceManifestLocation) + os.path.sep

        first_line = True
        for line in s_man:
            if first_line:
                first_line = False
                if line[0] == "#":
                    # get the type of the manifest
                    s_type = self.getManType(line)
                    if s_type != l_type:
                        print "Error: type of source manifest (%s) does not match type of local manifest (%s)" % (s_type, l_type)
                        return (None, None, None, None, None)
                else:
                    # no type specified
                    print "Error: type of source manifest is not specified. Is this a valid maniifest file?"
                    return (None, None, None, None, None)

                self.type = l_type
            if line[0] != "#":
                fields = line.rstrip().split("\t")
                # set the dict up as {path => [hash, size, seenLocal]
                source_man[fields[0]] = [fields[1], fields[2], False]

        # keep lists of modifications
        deleted = []
        addedDirs = []
        addedFiles = []
        modified = []

        with open(os.path.join(localManifestLocation, localManifestName)) as l_man:
            for line in l_man:
                if line[0] != "#":
                    fields = line.rstrip().split("\t")
                    try:
                        if source_man[fields[0]][0] != fields[1]:
                            # hashes don't match
                            modified.append(fields[0])
                        # seen this file
                        source_man[fields[0]][2] = True
                    except KeyError:
                        # this file has been deleted from the source manifest
                        deleted.append(fields[0])

        # check for new files
        for file in source_man.keys():
            if source_man[file][2] == False:
                if source_man[file][0] == '-':
                    addedDirs.append(file)
                else:
                    addedFiles.append(file)

        if printDiffs:
            new_size = 0
            modified_size = 0
            for file in addedFiles:
                new_size += int(source_man[file][1])
            for file in modified:
                modified_size += int(source_man[file][1])

            if len(addedFiles) > 0:
                print "#------------------------------------------------------"
                print "# Source contains %d new file(s) (%s)" % (len(addedFiles), self.formatData(new_size))
                for file in addedFiles:
                    print "\t".join([self.formatData(int(source_man[file][1])), file])

            if len(addedDirs) > 0:
                print "#------------------------------------------------------"
                print "# Source contains %d new folders(s)" % (len(addedDirs))
                for file in addedDirs:
                    print file

            if len(modified) > 0:
                print "#------------------------------------------------------"
                print "# Source contains %d modified file(s) (%s)" % (len(modified), self.formatData(modified_size))
                for file in modified:
                    print file

            if len(deleted) > 0:
                print "#------------------------------------------------------"
                print "# %d files have been deleted in the source:" % len(deleted)
                for file in deleted:
                    print file
        else:
            return (source,
                    [(a, source_man[a]) for a in addedFiles],
                    [(a, source_man[a]) for a in addedDirs],
                    deleted,
                    [(m, source_man[m]) for m in modified])


    def updateManifest(self,
                       localManifestLocation,
                       sourceManifestLocation,
                       localManifestName=None,
                       sourceManifestName=None,
                       prompt=True):
        """Update local files based on remote changes"""
        # get the diffs
        source, added_files, added_dirs, deleted, modified = self.diffManifests(localManifestLocation,
                                                                                sourceManifestLocation,
                                                                                localManifestName,
                                                                                sourceManifestName)
        # bail if the diff failed
        if source is None:
            return

        # no changes by default
        do_down = False
        do_del = False
        if prompt:
            total_size = 0
            for file in added_files:
                total_size += int(file[1][1])
            for file in modified:
                total_size += int(file[1][1])
            if total_size != 0:
                print "****************************************************************"
                print "%d new file(s) to be downloaded from source" % len(added_files)
                print "%d existing file(s) to be updated" % len(modified)
                print "%s will need to be downloaded" % self.formatData(total_size)
                do_down = self.promptUserDownload()
                if not do_down:
                    print "Download aborted"

            if len(deleted) > 0:
                print "****************************************************************"
                print "The following %d file(s) are scheduled to be removed" % len(deleted)
                for delete in deleted:
                    print delete
                do_del = self.promptUserDelete()
                if not do_del:
                    print "Deletion aborted"

        update_manifest = False
        # first delete
        if do_del:
            update_manifest = True
            deleted_dirs = []
            deleted_files = []
            for delete in deleted:
                full_path = os.path.abspath(os.path.join(localManifestLocation, delete))
                if os.path.isfile(full_path):
                    deleted_files.append(full_path)
                else:
                    deleted_dirs.append(full_path)
            for delete in deleted_dirs:
                shutil.rmtree(delete, ignore_errors=True)
            for delete in deleted_files:
                print delete
                os.remove(delete)

        if do_down:
            update_manifest = True
            for add in added_dirs:
                # make the dirs first
                full_path = os.path.abspath(os.path.join(localManifestLocation, add[0]))
                self.makeSurePathExists(full_path)
            for add in added_files:
                full_path = os.path.abspath(os.path.join(localManifestLocation, add[0]))
                urllib.urlretrieve(source+add[0], full_path)
            for modify in modified:
                full_path = os.path.abspath(os.path.join(localManifestLocation, modify[0]))
                urllib.urlretrieve(source+modify[0], full_path)

        if update_manifest:
            self.createManifest(localManifestLocation, manifestName=localManifestName)

    def getManType(self, line):
        """Work out the manifest type from the first line of the file"""
        return line.rstrip().split("##")[1]

    def formatData(self, amount):
        """Pretty print file sizes"""
        if amount < 1024*1024:
            return "%d B" % amount
        elif amount < 1024*1024*1024:
            return "%0.2f MB" % (float(amount)/(1024.*1024.))
        elif amount < 1024*1024*1024*1024:
            return "%0.2f GB" % (float(amount)/(1024.*1024.*1024.))
        elif amount < 1024*1024*1024*1024*1024:
            return "%0.2f TB" % (float(amount)/(1024.*1024.*1024.*1024.))

#-----------------------------------------------------------------------------
# FS utilities

    def makeSurePathExists(self, path):
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    def promptUserDownload(self):
        """Check that the user is OK with making changes"""
        input_not_ok = True
        minimal=False
        valid_responses = {'Y':True,'N':False}
        vrs = ",".join([x.lower() for x in valid_responses.keys()])
        while(input_not_ok):
            if(minimal):
                option = raw_input("Download? ("+vrs+") : ").upper()
            else:
                option = raw_input("Confirm you want to download this data\n" \
                                   "Changes *WILL* be permanent\n" \
                                   "Continue? ("+vrs+") : ").upper()
            if(option in valid_responses):
                print "****************************************************************"
                return valid_responses[option]
            else:
                print "ERROR: unrecognised choice '"+option+"'"
                minimal = True

    def promptUserDelete(self):
        """Check that the user is OK with making changes"""
        input_not_ok = True
        minimal=False
        valid_responses = {'Y':True,'N':False}
        vrs = ",".join([x.lower() for x in valid_responses.keys()])
        while(input_not_ok):
            if(minimal):
                option = raw_input("Delete files? ("+vrs+") : ").upper()
            else:
                option = raw_input("Confirm you want to delete these files\n" \
                                   "Changes *WILL* be permanent\n" \
                                   "Delete files? ("+vrs+") : ").upper()
            if(option in valid_responses):
                print "****************************************************************"
                return valid_responses[option]
            else:
                print "ERROR: unrecognised choice '"+option+"'"
                minimal = True


    def walk(self, parents, full_path, rel_path, dirs, files, skipFile=__MANIFEST__):
        """recursive walk through directory tree"""
        # first do files here
        for file in files:
            if file != skipFile:
                path = os.path.join(full_path, file)
                self.files.append(FE(file,
                                     rel_path,
                                     parents[-1],
                                     self.hashfile(path),
                                     os.path.getsize(path)
                                     )
                                  )
        for dir in dirs:
            # the walk will go into these dirs first
            tmp_fe = FE(dir, rel_path, parents[-1], "-", 0)
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
