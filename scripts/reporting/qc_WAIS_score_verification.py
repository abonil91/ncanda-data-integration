#!/usr/bin/env python
##
##  Copyright 2015 SRI International
##  License: https://ncanda.sri.com/software-license.txt
##
##  $Revision: 2110 $
##  $LastChangedBy: nicholsn $
##  $LastChangedDate: 2015-08-07 09:10:29 -0700 (Fri, 07 Aug 2015) $
##
"""
WAIS Score Verification
======================
Verifies whether the wais_rawscore was computed correctly.
"""
import os
import sys
import json
import csv

import redcap
import math
import pandas as pd

fields = ['study_id', 'redcap_event_name','exclude', 'visit_ignore',
          'visit_date','np_wais4_missing','np_wais4_rawscore',
          'np_wais4_rawscore_computed','np_wais4_rawscore_diff(correct)'];



def get_project_entry(args=None):
	"""
	Pulls the data from REDCap
	"""
	# Get API key.
	summary_key_file = open(os.path.join(os.path.expanduser("~"),
	                                     '.server_config',
	                                     'redcap-dataentry-token'), 'r')
	summary_api_key = summary_key_file.read().strip()

	# Connect to API.
	project_entry = redcap.Project('https://ncanda.sri.com/redcap/api/',
	                               summary_api_key, verify_ssl=False)
	return project_entry

def data_entry_fields(fields,project,arm):
	"""
	Gets the dataframe containing a specific arm from REDCap
	"""
	# Get a dataframe of fields
	data_entry_raw = project.export_records(fields=fields, format='df', events=[arm])
	return data_entry_raw

def value_check(idx,row):
	"""
	Checks to see if wais_rawscore and wais_rawscore_computed are equal
	"""
	# visit_ignore____yes with value 0 is not ignored
	error = dict()
	if math.isnan(row.get('exclude')):
		if row.get('visit_ignore___yes') != 1:
			# form is not missing if form_missing if value nan or zero
			if row.get('np_wais4_missing') != 1:
				if row.get('np_wais4_rawscore_computed') == row.get('np_wais4_rawscore_diff(correct)'):
					if row.get('np_wais4_rawscore_diff(correct)') != 0:
						error = dict(subject_site_id = idx[0],
							visit_date = row.get('visit_date'),
							event_name = idx[1],
							error = 'ERROR: WAIS score is not verified'
							)
	return error

def main(args=None):
	project_entry = get_project_entry()
	project_df = data_entry_fields(fields,project_entry,'1y_visit_arm_1')
	error = []
	# Try using `for` loops rather than `while` to be `pythonic`... this looks like java or c =)
	for idx, row in project_df.iterrows():
		check = value_check(idx,row)
		if check:
			error.append(check)

	for e in error:
		if e != 'null':
			print json.dumps(e, sort_keys = True)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    argv = parser.parse_args()
    sys.exit(main(args=argv))