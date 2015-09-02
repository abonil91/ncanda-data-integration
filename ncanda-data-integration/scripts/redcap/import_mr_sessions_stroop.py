#!/usr/bin/env python

##
##  Copyright 2015 SRI International
##  License: https://ncanda.sri.com/software-license.txt
##
##  $Revision: 2110 $
##  $LastChangedBy: nicholsn $
##  $LastChangedDate: 2015-08-07 09:10:29 -0700 (Fri, 07 Aug 2015) $
##

import os
import re
import tempfile
import shutil
import subprocess

#
# Check for Stroop data (ePrime log file) in given XNAT session
#
import_bindir = os.path.join( os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) ), 'import', 'laptops' )
bindir = os.path.dirname( os.path.abspath(__file__) )

# Check a list of experiments for ePrime Stroop files
def check_for_stroop( xnat, xnat_eid_list, verbose=False ):
    stroop_files = []
    for xnat_eid in xnat_eid_list:
        experiment = xnat.select.experiment( xnat_eid )

        # Get list of resource files that match the Stroop file name pattern
        for resource in  experiment.resources().get():
            resource_files = xnat._get_json( '/data/experiments/%s/resources/%s/files?format=json' % ( xnat_eid, resource ) );
            stroop_files += [ (xnat_eid, resource, re.sub( '.*\/files\/', '', file['URI']) ) for file in resource_files if re.match( '^NCANDAStroopMtS_3cycles_7m53stask_.*.txt$', file['Name'] ) ]
        
    # No matching files - nothing to do
    if len( stroop_files ) == 0:
        return (None, None, None) 

    # Get first file from list, warn if more files
    if len( stroop_files ) > 1:
        print "ERROR: experiment(s)",','.join(xnat_eid_list),"have/has more than one Stroop .txt file. Please make sure there is exactly one per session."
	return (None, None, None)

    return stroop_files[0]


# Import a Stroop file into REDCap after scoring
def import_stroop_to_redcap( xnat, stroop_eid, stroop_resource, stroop_file, redcap_token, redcap_key, verbose=False, no_upload=False ):
    if verbose:
        print "Importing Stroop data from file %s:%s" % ( stroop_eid, stroop_file )

    # Download Stroop file from XNAT into temporary directory
    experiment = xnat.select.experiment( stroop_eid )
    tempdir = tempfile.mkdtemp()
    stroop_file_path = experiment.resource( stroop_resource ).file( stroop_file ).get_copy( os.path.join( tempdir, stroop_file ) )

    # Convert downloaded Stroop file to CSV scores file
    added_files = []
    try:
        added_files = subprocess.check_output( [ os.path.join( import_bindir, "stroop2csv" ), '--mr-session', '--record', redcap_key[0], '--event', redcap_key[1], stroop_file_path, tempdir ] )
    except:
        pass

    if len( added_files ):
        if not no_upload:
            # Upload CSV file(s) (should only be one anyway)
            for file in added_files.split( '\n' ):
                if re.match( '.*\.csv$', file ):
                    if verbose:
                        print "Uploading ePrime Stroop scores",file
                    subprocess.call( [ os.path.join( bindir, 'csv2redcap' ), file ] )            
            # Upload original ePrime file for future reference
            if verbose:
                print "Uploading ePrime Stroop file",stroop_file_path
            subprocess.check_output( [ os.path.join( import_bindir, "eprime2redcap" ), "--api-key", redcap_token, '--record', redcap_key[0], '--event', redcap_key[1], stroop_file_path, 'mri_stroop_log_file' ] )
    else:
        print "ERROR: could not convert Stroop file %s:%s" % ( xnat_eid, stroop_file )

    shutil.rmtree( tempdir )

