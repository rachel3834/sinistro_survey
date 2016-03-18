# -*- coding: utf-8 -*-
"""
Created on Wed Mar 16 14:51:42 2016

@author: rstreet
"""

#############################################################################
#                       SINISTRO SURVEY
#
# Observation control software designed to run in survey-mode on the LCOGT
# telescope network using the Sinistro instruments
#############################################################################

import config_parser
import log_utilities
import survey_classes
from os import path, remove
from datetime import datetime

def run_survey():
    """Driver function for the Sinistro survey package"""
    
    # Parse script configuration
    fconfig = 'survey_config.xml'
    lconfigsdir = '.survey'
    (iexec, script_config) = config_parser.readxmlconfig(fconfig,lconfigsdir)
    
    # Start logging
    log = log_utilities.start_day_log( script_config, 'sinistro_survey_obs' )

    # Check for clashing ongoing processes for which the logs might 
    # become corrupted if this script runs at the same time.  
    # If not present, create a lock to prevent other crashes.
    lock( script_config, 'check', log )
    lock( script_config, 'lock', log )
    
    # Read targetlist and observation configurations
    target_fields = read_target_list( script_config, log )
    
    # Check the logs for any pre-existing and still live obs requests:
    existing_obs = read_obs_record( script_config, log )
    
    # Build observing requests and submit, excluding any fields for which
    # live observation requests should already be in the scheduler:
    obsrecord = log_utilities.start_obs_record( script_config )
    for target_name, field in target_fields.items():
        
        if field.name not in existing_obs.keys():
            field.build_odin_request( script_config, log=log, debug=True )
            log.info('Built observation request ' + field.request_id)
            
            field.submit_request(script_config, log=log, debug=True)
            log.info('    => Status: ' + field.submit_status + \
                                ': ' + field.submit_response)
            obsrecord.write( field.obs_record( script_config ) )
        else:
            log.info('Existing live observation request for field ' + \
                field.name + ' - no additional request made')
                
    # Tidy up and finish:
    obsrecord.close()
    log.info('Finished requesting observations')
    lock( script_config, 'unlock', log )
    log_utilities.end_day_log( log )

def lock( config, state, log ):
    """Method to create and release this script's lockfile and also to determine
    whether another lock file exists which may prevent this script operating.    
    """

    lock_file = path.join( config['logdir'], 'survey.lock' )    

    if state == 'lock':
        lock = open(lock_file,'w')
        ts = datetime.utcnow()
        lock.write( ts.strftime("%Y-%m-%dT%H:%M:%S") )
        lock.close()
        log.info('Created lock file')
    
    elif state == 'unlock':
        if path.isfile(lock_file) == True:
            remove( lock_file )
            log.info('Removed lock file')
    
    elif state == 'check':
        lock_list = [ 'obscontrol.lock', 'survey.lock' ]
        for lock_name in lock_list:
            lock_file = path.join( config['logdir'],lock_name )
            if path.isfile( lock_file ) == True:
                log.info('Clashing lock file encountered ( ' + lock_name + \
                                ' ), halting')
                log_utilities.end_day_log( log )
                exit()
        log.info('Checked for clashing locks; found none')
        
def read_target_list( script_config, log ):
    """Function to parse the list of field pointings to be surveyed and the
    observation sequence to be done at each pointing"""
    
    target_file = path.join( script_config['logdir'], script_config['targetlist'] )
    if path.isfile( target_file ) == False:
        log.info('ERROR: Cannot find target list file ' + target_file)
        log.info('HALTING: No observations possible')
        log_utilities.end_day_log( log )
        exit()
    
    file_lines = open( target_file, 'r' ).readlines()

    target_fields = {}
    if file_lines[0].lstrip()[0:1] != '#':
        log.info('ERROR: Improperly formatted TargetList file; need header parameters')
        log_utilities.end_day_log( log )
        exit()
        
    for line in file_lines[1:]:
        if line.lstrip()[0:1] != '#':
            field = survey_classes.SurveyField()
            entries = line.replace('#','').replace('\n','').split()
            field.name = entries[0]
            field.ra = entries[1]
            field.dec = entries[2]
            field.site = entries[3]
            field.observatory = entries[4]
            field.tel = entries[5]
            field.instrument = entries[6]
            field.filter = entries[7]
            exp_time_list = entries[8].split(',')
            nexp_list = entries[9].split(',')
            for exp in exp_time_list:
                field.exposure_times.append( float(exp) )
            for nexp in nexp_list:
                field.exposure_counts.append( int(nexp) )
            field.cadence = float(entries[10])

            target_fields[field.name] = field
    
    return target_fields

def read_obs_record( script_config, log ):
    """Function to read the log of recently submitted observations"""
    
    # Get the paths for the current log and the one from the day before,
    # to mitigate in case we're close to the date rollover
    log_file1 = log_utilities.get_log_path( script_config['logdir'], \
                                    'ObsRecord_1m' )
    log_file2 = log_utilities.get_log_path( script_config['logdir'], \
                                    'ObsRecord_1m',day_offset=1 )
    log.info('Searching logs for any previous requests that are still ongoing:')
    log.info(log_file1 + '\n' + log_file2)
    
    existing_obs = {}
    tnow = datetime.utcnow()
    
    # Case 1: no recent observations have been requested
    if path.isfile( log_file1 ) == False and path.isfile( log_file2 ) == False:
        log.info('-> No records of recent observations have been found')
        return existing_obs
    
    # Case 2: Recent logs exist, indicating previous observation groups may
    # still be live.  Note that these logs contain ALL observation requests, 
    # survey or not, so we first filter for those prefixed 'RBNS'
    else:
        for log_file in [ log_file1, log_file2 ]:
            if path.isfile( log_file ) == True:
                file_lines = open(log_file, 'r').readlines()
                for line in file_lines:
                    if line.lstrip()[0:1] != '#':
                        entries = line.split()
                        if 'RBNS' in entries[0]:
                            field = survey_classes.SurveyField()
                            field.name = entries[7]
                            field.request_id = entries[0]
                            field.ts_submit = datetime.strptime( entries[17], \
                                                            "%Y-%m-%dT%H:%M:%S" )
                            field.ts_expire = datetime.strptime( entries[18], \
                                                            "%Y-%m-%dT%H:%M:%S" )
                            field.submit_status = entries[-1]
                            
                            if field.submit_status == 'add_OK' and \
                                field.ts_expire > tnow:
                                existing_obs[field.name] = field
                                log.info(' -> Found ongoing live obs request for field ' + \
                                        field.name + ': ' + field.request_id + \
                                        '. Expires: ' + \
                                        field.ts_submit.strftime("%Y-%m-%dT%H:%M:%S"))
    return existing_obs

if __name__ == '__main__':
    run_survey()
    
