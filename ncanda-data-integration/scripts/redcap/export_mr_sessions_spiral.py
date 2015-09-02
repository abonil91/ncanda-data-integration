#!/usr/bin/env python

##
##  Copyright 2015 SRI International
##  License: https://ncanda.sri.com/software-license.txt
##
##  $Revision: 2110 $
##  $LastChangedBy: nicholsn $
##  $LastChangedDate: 2015-08-07 09:10:29 -0700 (Fri, 07 Aug 2015) $
##

import re
import os
import os.path
import subprocess
import shutil
import fnmatch
import tempfile
import sys

def export_spiral_files(xnat, resource_location, to_directory, stroop=(None,None,None), verbose=None):
    result = False # Nothing updated or created yet
    # resource location contains results dict with path building elements
    # NCANDA_E01696/27630/spiral.tar.gz
    spiral_nifti_out = os.path.join(to_directory, 'native', 'bold4D.nii.gz' )
    if not os.path.exists( spiral_nifti_out ):
        tmpdir = tempfile.mkdtemp()
        result = do_export_spiral_files( xnat, resource_location, to_directory, spiral_nifti_out, tmpdir )
        shutil.rmtree(tmpdir)

    # Do we have information on Stroop files?
    if stroop[0] != None:
        stroop_file_out = os.path.join(to_directory, 'native', 'stroop.txt' )
        # Stroop file does not exist yet, so create it
        if not os.path.exists( stroop_file_out ):
            tmpdir = tempfile.mkdtemp()
            stroop_file_tmp = xnat.select.experiment( stroop[0] ).resource( stroop[1] ).file( stroop[2] ).get_copy( os.path.join( tmpdir, stroop[2] ) )

            from sanitize_eprime import copy_sanitize
            copy_sanitize( stroop_file_tmp, stroop_file_out )
            shutil.rmtree(tmpdir)

            result = True

    return result

def do_export_spiral_files( xnat, resource_location, to_directory, spiral_nifti_out, tmpdir, verbose=None ):
    # Do the actual export using a temporary directory that is managed by the caller (simplifies its removal regardless of exit taken)
    [ xnat_eid, resource_id, resource_file_bname ] = resource_location.split('/')
    tmp_file_path = xnat.select.experiment( xnat_eid ).resource( resource_id ).file( resource_file_bname ).get_copy( os.path.join( tmpdir, "pfiles.tar.gz" ) )

    errcode, stdout, stderr = untar_to_dir( tmp_file_path, tmpdir )
    if errcode != 0:
        print "ERROR: unable to un-tar resource file",resource_location
        print "StdErr:\n",stderr
        print "StdOut:\n",stdout
        return False

    spiral_E_files = glob_for_files_recursive( tmpdir, pattern="E*P*.7" )
    if len( spiral_E_files ) > 1:
        print "ERROR: more than one E file found.\n"
        print '\n'.join( spiral_E_files )
        return False

    physio_files = glob_for_files_recursive( tmpdir, pattern="P*.physio" )
    if len( physio_files ) > 1:
        print "ERROR: more than one physio file found.\n"
        print '\n'.join( physio_files )
        return False

    if len( spiral_E_files ) == 1:
        # Make directory first
        spiral_dir_out = os.path.join( to_directory, 'native' )
        if not os.path.exists( spiral_dir_out ):
            os.makedirs( spiral_dir_out )
        # Now try to make the NIfTI
        errcode, stdout, stderr = make_nifti_from_spiral(spiral_E_files[0], spiral_nifti_out)
        if not os.path.exists( spiral_nifti_out ):
            print "ERROR: unable to make NIfTI from resource file {0}. Please try running makenifti manually.".format(resource_location)
            if verbose:
                print "StdErr:\n",stderr
                print "StdOut:\n",stdout
            return False
    else:
        print "ERROR: no spiral data file found in",resource_location
        return False

    if len( physio_files ) == 1:
        spiral_physio_out = os.path.join(to_directory, 'native', 'physio' )
        shutil.copyfile( physio_files[0], spiral_physio_out )
	gzip( spiral_physio_out )

    return True


def make_nifti_from_spiral(spiral_file, outfile):
    cmd = "makenifti -s 0 %s %s" %(spiral_file, outfile[:-7])

    errcode, stdout, stderr = call_shell_program(cmd)
    if os.path.exists( outfile[:-3] ):
        gzip( outfile[:-3] )

    return errcode, stdout, stderr

def call_shell_program( cmd ):
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    return process.returncode, out, err

def untar_to_dir(tarfile, out_dir):
    cmd = "tar -xzf %(tarfile)s --directory=%(out_dir)s"

    cmd = cmd %{'tarfile':tarfile,
                'out_dir':out_dir
                }

    errcode, stdout, stderr = call_shell_program(cmd)
    return errcode, stdout, stderr

def glob_for_files_recursive(root_dir, pattern):
    '''Globs for files with the pattern rules used in bash. '''

    match_files = []
    for root, dirs, files in os.walk( root_dir, topdown=False ):
        match_files += [ os.path.join( root, fname ) for fname in files if fnmatch.fnmatch( fname, pattern ) ]

    return match_files

def gzip(infile):
    cmd = 'gzip -9 %s' %infile
    call_shell_program(cmd)
