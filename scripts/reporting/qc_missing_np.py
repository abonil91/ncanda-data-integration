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
Missing NP
======================
Generate a report indicating which NPs have not been entered.
"""
import os
import sys
import json
import csv

import redcap
import math
import pandas as pd

# Fields
fields = ['study_id', 'redcap_event_name','exclude', 'visit_ignore',
          'visit_date','visit_notes', 'np_notes', 'bio_np_missing', 'bio_np_date',
          'dd1000_missing','dd1000_date', 'dd100_missing','dd100_date','np_wrat4_missing',
          'np_wrat4_wr_raw','np_gpeg_missing','np_gpeg_exclusion','np_gpeg_dh_time','np_gpeg_ndh_time', 
          'np_reyo_missing','np_reyo_copy_time', 'np_atax_missing','np_atax_sht_trial1', 
          'np_wais4_missing', 'np_wais4_corr15s', 'pasat_missing','pasat_date', 
          'cnp_missing','cnp_test_sessions_dotest','stroop_missing',
          'stroop_date', 'mri_stroop_missing','mri_stroop_date'];

np_fields = [['bio_np_missing', 'bio_np_date'],['dd1000_missing','dd1000_date'], 
			['dd100_missing','dd100_date'],['np_wrat4_missing','np_wrat4_wr_raw'],
          ['np_reyo_missing','np_reyo_copy_time'], ['np_atax_missing','np_atax_sht_trial1'], 
          ['np_wais4_missing', 'np_wais4_corr15s'], ['pasat_missing','pasat_date'], 
          ['cnp_missing','cnp_test_sessions_dotest'],['stroop_missing',
          'stroop_date']];

np_gpeg_fields = [['np_gpeg_exclusion___dh','np_gpeg_dh_time'],['np_gpeg_exclusion___ndh',
'np_gpeg_ndh_time']]

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
	Gets the dataframe containing data for specific event from REDCap
	"""
	# Get a dataframe of fields
	data_entry_raw = project.export_records(fields=fields, format='df', events=[arm])
	return data_entry_raw

def value_check(idx,row,field_missing, field_value):
	"""
	Checks to see if an NP is missing
	"""
	# visit_ignore____yes with value 0 is not ignored
	error = dict()
	if math.isnan(row.get('exclude')):
		if row.get('visit_ignore___yes') == 0:
			# np is not missing if field_missing if value nan or zero
			if row.get(field_missing) == 0 or math.isnan(row.get(field_missing)):
				# for np_date, date is stored as a string
				if type(row.get(field_value)) == float:
					# If field is left blank, a NaN is put in it's place
					if math.isnan(row.get(field_value)):
						error = dict(subject_site_id = idx[0],
							visit_date = row.get('visit_date'),
							np_missing = field_missing,
							event_name = idx[1],
							error = 'ERROR: NP is missing.'
							)
	return error

def np_groove_check(idx,row,field_missing, field_excluded, field_value):
	"""
	Checks to see if the Grooveboard NP is missing
	"""
	# visit_ignore____yes with value 0 is not ignored
	error = dict()
	if math.isnan(row.get('exclude')):
		if row.get('visit_ignore___yes') == 0:
			# np is not missing if field_missing if value nan or zero
			if row.get(field_excluded) == 0:
				# np is not excluded if field_missing if value nan or zero
				if row.get(field_missing) == 0 or math.isnan(row.get(field_missing)):
					# for np_date, date is stored as a string
					if type(row.get(field_value)) == float:
						# If field is left blank, a NaN is put in it's place
						if math.isnan(row.get(field_value)):
							error = dict(subject_site_id = idx[0],
								visit_date = row.get('visit_date'),
								np_missing = field_missing,
								event_name = idx[1],
								error = 'ERROR: NP is missing.'
								)
	return error


def main(args=None):
	project_entry = get_project_entry()
	project_df = data_entry_fields(fields,project_entry,'1y_visit_arm_1')
	error = []
	# Try using `for` loops rather than `while` to be `pythonic`... this looks like java or c =)
	for idx, row in project_df.iterrows():
		for np in np_fields:
			check = value_check(idx,row,np[0],np[1])
			if check:
				error.append(check)
		for np in np_gpeg_fields:
			check = np_groove_check(idx,row,'np_gpeg_missing',np[0],np[1])
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




