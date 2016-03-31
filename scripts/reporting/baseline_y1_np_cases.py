#!/usr/bin/env python
##
##  Copyright 2016 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
##"""
Baseline cases

This script generates a list of all subject that have a valid baseline and follow-up visit.
"""
import os

import pandas
import redcap

# First REDCap connection for the Summary project (this is where we put data)
summary_key_file = open(os.path.join( os.path.expanduser("~"), '.server_config/redcap-dataentry-token' ), 'r')
summary_api_key = summary_key_file.read().strip()
rc_summary = redcap.Project('https://ncanda.sri.com/redcap/api/', summary_api_key, verify_ssl=False)

# Get all np reports for baseline and 1r
visit  = rc_summary.export_records(fields=['study_id', 'exclude', 'visit_ignore___yes'],
                                 forms=['mr_session_report','visit_date'],
                                 events=['baseline_visit_arm_1', '1y_visit_arm_1'], 
                                 format='df')

# Create filters for cases that are included
visit_included = visit.exclude != 1
np_collected = visit.visit_ignore___yes != 1

# Apply filters for results
results = visit[visit_included & np_collected]

results.to_csv('baseline_y1_np_case.csv', columns = ['exclude','visit_ignore___yes', 'mri_xnat_sid','mri_xnat_eids'])

