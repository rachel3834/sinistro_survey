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
    
    if path.isfile(log_file) == True:
        obsrecord = open(log_file,'a')
    else:
        obsrecord = open(log_file,'w')
        obsrecord.write('# Log of Requested Observation Groups\n')
        obsrecord.write('#\n')
        obsrecord.write('# Log started: 2015-11-04 T 00:00:10\n')
        obsrecord.write('# Running at sba\n')
        obsrecord.write('#\n')
        obsrecord.write('# GrpID  TrackID  ReqID  Network  Site  Obs  Tel  Instrum  Target  RA(J2000)  Dec(J2000)  Filter  ExpTime  ExpCount  ExpTaken  GrpType  Cadence  Priority  TS_Submit  TS_Expire  TAGID  UserID  PropID  TTL  Twilight  Darkness  Seeing  FocusOffset  RotatorAngle  Autoguider  SubmitMech  ConfigType  ReqOrigin  RCS_Report\n')
    return obsrecord
