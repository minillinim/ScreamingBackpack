# ScreamingBackpack

## Overview

A utility for handing syncing of remote and local data resources. Developed for use in CheckM but hopefully generic enough to be used elsewhere.

## Installation

Should be as simple as

    pip install ScreamingBackpack

## Example usage

The utility works by placing a small file (manifest file) in the data directory that describes the file names, their locations and if possible their hashes (sha256).
This file is downloaded during diff and update functions and is used to determine what other file operations (downloads / deletions) should occur.

The format of the manifest file is very simple. The first line is a header which describes the manifest type and some other info;

     ##<TYPE>## Data manifest created by ScreamingBackpack version <VERSION>

     where: <TYPE> is user specified and <VERSION> is the version of SBP that created the file

Each line below the header describes a file or folder which is under management. File lines look like this:

    3   d37b38c8411e250f55393442db47eed954354898fa958c93047d7a66956880cb    5000

    I.e. A three column file in the format "local_path   sha256_hash    size_in_bytes"

Folder lines look like this:

    9   -   0

    I.e. a file line with no size or hash.

The binary screamingBackpack can be run in three modes:

  create        - create a new manifest file
  diff          - work out the difference between two manifests and print out the results
  update        - update the local data repo tp reflect any changes made at the remote source

The bin file very simply wraps these functions which are available by importing like this

    from screamingBackpack.manifestManager import ManifestManager

    MM = ManifestManager(manType="<TYPE>")

    MM.createManifest(pathToManifest,           # path to the root folder of the data to be managed
                      manifestName=None)        # specify a custom name for the manifest file (default = .dmanifest)

    MM.diffManifests(localManifestLocation,     # path to local data repo
                     sourceManifestLocation,    # path to source or fully qualified remote url
                     localManifestName=None,
                     sourceManifestName=None,
                     printDiffs=True)           # Print to stdout and exit

    MM.updateManifest(localManifestLocation,
                      sourceManifestLocation,
                      localManifestName=None,
                      sourceManifestName=None,
                      prompt=True)              # prompt user before making changes

## Help

If you experience any problems using ScreamingBackpack, open an [issue](https://github.com/minillinim/ScreamingBackpack/issues) on GitHub and tell us about it.

## Licence and referencing

Project home page, info on the source tree, documentation, issues and how to contribute, see http://github.com/minillinim/ScreamingBackpack

This software is currently unpublished

## Copyright

Copyright (c) 2014 Michael Imelfort. See LICENSE.txt for further details.
