# -*- coding: utf-8 -*-
"""
Created on Wed Feb 17 00:00:05 2016

@author: robouser
"""

#############################################################################
#                       LOGGING UTILITIES
#############################################################################

import logging
from os import path
from astropy.time import Time, TimeDelta
import glob
from datetime import datetime
import survey_classes

def get_log_path( log_dir, log_root_name, day_offset=None ):
    """Function to return the full path to a timestamped day log"""

    ts = Time.now()
    if day_offset != None:
        dt = TimeDelta( (float(day_offset)*24.0*60.0*60.0), format='sec' )
        ts = ts + dt
    ts = ts.iso.split()[0]
        
    log_file = path.join( log_dir, log_root_name + '_' + ts + '_sba.log' )
    return log_file

def start_day_log( config, log_name, console_output=False ):
    """Function to initialize a new log file.  The naming convention for the
    file is [log_name]_[UTC_date].log.  A new file is automatically created 
    if none for the current UTC day already exist, otherwise output is appended
    to an existing file.
    This function also configures the log file to provide timestamps for 
    all entries.  
    """

    log_file = get_log_path( config['logdir'], config['log_root_name'] )

    # Look for previous logs and rollover the date if the latest log
    # isn't from the curent date:


    # To capture the logging stream from the whole script, create
    # a log instance together with a console handler.  
    # Set formatting as appropriate.
    log = logging.getLogger( log_name )
    
    if len(log.handlers) == 0:
        log.setLevel( logging.INFO )
        file_handler = logging.FileHandler( log_file )
        file_handler.setLevel( logging.INFO )
        
        if console_output == True:
            console_handler = logging.StreamHandler()
            console_handler.setLevel( logging.INFO )
    
        formatter = logging.Formatter( fmt='%(asctime)s %(message)s', \
                                    datefmt='%Y-%m-%dT%H:%M:%S' )
        file_handler.setFormatter( formatter )
        if console_output == True:
            console_handler.setFormatter( formatter )
    
        log.addHandler( file_handler )
        if console_output == True:
            log.addHandler( console_handler )
    
    log.info( '\n------------------------------------------------------\n')
    return log
    
def end_day_log( log ):
    """Function to cleanly shutdown logging functions with last timestamped
    entry"""
    
    log.info( 'Processing complete\n' )
    logging.shutdown()

def start_obs_record( config ):
    """Function to initialize or open a daily record of submitted observations"""
    
    log_file = get_log_path( config['logdir'], 'ObsRecord_1m_' )
    
    tnow = datetime.utcnow()
    
    if path.isfile(log_file) == True:
        obsrecord = open(log_file,'a')
    else:
        obsrecord = open(log_file,'w')
        obsrecord.write('# Log of Requested Observation Groups\n')
        obsrecord.write('#\n')
        obsrecord.write('# Log started: ' + tnow.strftime("%Y-%m-%dT%H:%M:%S") + '\n')
        obsrecord.write('# Running at sba\n')
        obsrecord.write('#\n')
        obsrecord.write('# GrpID  TrackID  ReqID  Network  Site  Obs  Tel  Instrum  Target  RA(J2000)  Dec(J2000)  Filter  ExpTime  ExpCount  ExpTaken  GrpType  Cadence  Priority  TS_Submit  TS_Expire  TAGID  UserID  PropID  TTL  Twilight  Darkness  Seeing  FocusOffset  RotatorAngle  Autoguider  SubmitMech  ConfigType  ReqOrigin  RCS_Report\n')
    return obsrecord

def read_active_survey_obs( config, log ):
    """Function to read the ActiveSurveyObs.log file"""
    
    log_file = path.join( config['logdir'], 'ActiveSurveyObs.log' )
    
    existing_obs = {}    
    
    tnow = datetime.utcnow()
    
    # Case 1: no log file.  Assume no recent observations have been requested
    if path.isfile( log_file ) == False:
        log.info('-> No records of recent observations have been found')
        return existing_obs
    
    # Case 2: A log file exists, indicating previous observation groups may
    # still be live.  Note we first filter for those prefixed 'RBNS'
    else:
        file_lines = open(log_file, 'r').readlines()
        log.info('Reading log file ' + path.basename( log_file ))
        for line in file_lines:
            if line.lstrip()[0:1] != '#' and len(line) > 0:
                entries = line.split()
                if 'RBNS' in entries[0]:
                    field = survey_classes.SurveyField(config)
                    field.set_pars_from_log( line )
                    if field.submit_status == 'add_OK' and \
                        field.ts_expire > tnow:
                        existing_obs[field.name] = field
                        log.info(' -> Found ongoing live obs request for field ' + \
                                field.name + ': ' + field.req_id + \
                                '. Expires: ' + \
                                field.ts_submit.strftime("%Y-%m-%dT%H:%M:%S"))
        if len(existing_obs) == 0:
            log.info(' -> No ongoing observations found')
            
    return existing_obs

def write_active_survey_obs( existing_obs, config, log ):
    """Function to write the ActiveSurveyObs log"""
    
    log_file = path.join( config['logdir'], 'ActiveSurveyObs.log' )
    tnow = datetime.utcnow()
    active_log = open( log_file, 'w' )
    active_log.write('# Log of Requested Observation Groups\n')
    active_log.write('#\n')
    active_log.write('# Log started: ' + tnow.strftime("%Y-%m-%dT%H:%M:%S") + '\n')
    active_log.write('# Running at sba\n')
    active_log.write('# GrpID  TrackID  ReqID  Network  Site  Obs  Tel  Instrum  Target  RA(J2000)  Dec(J2000)  Filter  ExpTime  ExpCount  ExpTaken  GrpType  Cadence  Priority  TS_Submit  TS_Expire  TAGID  UserID  PropID  TTL  Twilight  Darkness  Seeing  FocusOffset  RotatorAngle  Autoguider  SubmitMech  ConfigType  ReqOrigin  RCS_Report\n')
    for field_id, field in existing_obs.items():
        obsrecord = field.obs_record( config )
        active_log.write( obsrecord )
    active_log.close()
    log.info('Completed output of observations to active log')