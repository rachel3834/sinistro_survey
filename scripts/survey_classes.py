# -*- coding: utf-8 -*-
"""
Created on Wed Mar 16 15:24:24 2016

@author: rstreet
"""

from datetime import datetime, timedelta
import urllib
import utilities
import instruments
import json
import httplib
from sys import exit

class SurveyField:
    
    def __init__(self, config):
        self.name = None
        self.track_id = None
        self.req_id = None
        self.network = 'LCOGT'
        self.ra = None
        self.dec = None
        self.site = None
        self.observatory = None
        self.tel = None
        self.instrument = None
        self.instrument_class = None
        self.filter = None
        self.exposures_taken = 0
        self.group_type = 'Monitor'
        self.exposure_times = []
        self.exposure_counts = []
        self.cadence = None
        self.priority = 'Medium'
        self.json_request = None
        self.group_id = None
        self.request_number = None
        self.ts_submit = None
        self.ts_expire = None
        self.tag_id = 'LCOGT'
        self.user_id = config['user_id']
        self.proposal_id = config['proposal_id']
        self.ttl = 1.0
        self.twilight = 'Yes'
        self.darkness = 'Bright'
        self.seeing = 'Good'
        self.focus_offset = '0'
        self.rotator_angle = '0'
        self.autoguider = 'maybe'
        self.submit_mech = 'ODIN'
        self.config_type = 'network'
        self.req_origin = 'survey'
        self.submit_response = None
        self.submit_status = None
        
    def summary(self):
        exp_list = ''
        for exp in self.exposures:
            exp_list = exp_list + ' ' + str(exp)
            
        output = str(self.name) + ' ' + str(self.ra) + ' ' + str(self.dec) + \
                ' ' + str(self.site) + ' ' + str(self.observatory) + ' ' + \
                ' ' + str(self.instrument) + ' ' + str(self.filter) + ' ' + \
                exp_list + ' ' + str(self.cadence)
        return output

    def get_group_id(self):
        dateobj = datetime.utcnow()
        time = float(dateobj.hour) + (float(dateobj.minute)/60.0) + \
        (float(dateobj.second)/3600.0) + (float(dateobj.microsecond)/3600e6)
        time = round(time,8)
        ctime = str(time)
        date = dateobj.strftime('%Y%m%d')
        TS = date+'T'+ctime
        self.group_id = 'RBNS'+TS
    
    def set_pars_from_log(self, log_entry):
        entries = log_entry.replace('\n','').split()
        self.group_id = entries[0]
        self.track_id = entries[1]
        self.req_id = entries[2]
        self.network = entries[3]
        self.site = entries[4]
        self.observatory= entries[5]
        self.tel = entries[6]
        self.instrument = entries[7]
        self.instrument_class = entries[7]
        self.name = entries[8]
        self.ra = entries[9]
        self.dec = entries[10]
        self.filter = entries[11]
        self.exposure_times.append(float(entries[12]))
        self.exposure_counts.append(int(entries[13]))
        self.exposures_taken = int(entries[14])
        self.group_type = entries[15]
        self.cadence = entries[16]
        self.priority = entries[17]
        self.ts_submit = datetime.strptime( entries[18], \
                                        "%Y-%m-%dT%H:%M:%S" )
        self.ts_expire = datetime.strptime( entries[19], \
                                        "%Y-%m-%dT%H:%M:%S" )
        self.tag_id = entries[20]
        self.user_id = entries[21]
        self.proposal_id = entries[22]
        self.ttl = entries[23]
        self.twilight = entries[24]
        self.darkness = entries[25]
        self.seeing = entries[26]
        self.focus_offset = entries[27]
        self.rotator_angle = entries[28]
        self.autoguider = entries[29]
        self.submit_mech = entries[30]
        self.config_type = entries[31]
        self.req_origin = entries[32]
        self.submit_status = entries[33]
    
    def build_odin_request(self, config, log=None, debug=False):
        
        proposal = { 
                    'proposal_id': config['proposal_id'],
                    'user_id'    : config['user_id'] 
                    }
        if debug == True and log != None:
            log.info('Building ODIN observation request')
            log.info('Proposal dictionary: ' + str( proposal ))
            
        location = {
                    'telescope_class' : str(self.tel).replace('a',''),
                    'site':             str(self.site),
                    'observatory':      str(self.observatory)
                    }
        if debug == True and log != None:
            log.info('Location dictionary: ' + str( location ))
            
        (ra_deg, dec_deg) = utilities.sex2decdeg(self.ra, self.dec)
        target =   {
                    'name'		   : str(self.name),
                    'ra'		   : ra_deg,
                    'dec'		   : dec_deg,
                    'proper_motion_ra'  : 0, 
                    'proper_motion_dec' : 0,
                    'parallax'	   : 0, 
                    'epoch'  	   : 2000,	  
                    }
        if debug == True and log != None:
            log.info('Target dictionary: ' + str( target ))
            
        constraints = { 
        		  'max_airmass': 2.0
                    }
        if debug == True and log != None:
            log.info('Constraints dictionary: ' + str( constraints ))
            
        imager = instruments.Instrument(self.tel, self.instrument)
        self.instrument_class = imager.instrument_class
        if debug == True and log != None:
            log.info('Instrument overheads ' + imager.summary() )
            
        self.get_group_id()   
        ur = { 'group_id': self.group_id, 'operator': 'many' }
        reqList = []
        
        self.ts_submit = datetime.utcnow() + timedelta(seconds=(10*60))
        self.ts_expire = self.ts_submit + timedelta(seconds=(self.ttl*24*60*60))
        request_start = self.ts_submit
        while request_start < self.ts_expire:
            molecule_list = []
            
            for i,exptime in enumerate(self.exposure_times):
            	nexp = self.exposure_counts[i]
            	defocus = 0.0
        
            	molecule = { 
            		 # Required fields
            		 'exposure_time'   : exptime,    
            		 'exposure_count'  : nexp,	     
            		 'filter'	   : self.filter,      
            		 
            		 'type' 	   : 'EXPOSE',      
            		 'ag_name'	   : '',	     
            		 'ag_mode'	   : 'Optional',
            		 'instrument_name' : imager.instrument,
            		 'bin_x'	   : 1,
            		 'bin_y'	   : 1,
            		 'defocus'	   : defocus      
            	       }
                if debug == True and log != None:
                    log.info(' -> Molecule: ' + str(molecule))
    
            	molecule_list.append(molecule)
            
            window = float(config['request_window']) * 60.0 * 60.0
            exposure_group_length = imager.calc_group_length( nexp, exptime )
            request_end = request_start + \
                     timedelta( seconds= ( exposure_group_length + window ) )

            req = { 'observation_note':'',
                    'observation_type': 'NORMAL', 
                    'target': target , 
                    'windows': [ { 'start': request_start.strftime("%Y-%m-%d %H:%M:%S"), 
                                   'end': request_end.strftime("%Y-%m-%d %H:%M:%S") } ],
                    'fail_count': 0,
                    'location': location,
                    'molecules': molecule_list,
                    'type': 'request', 
                    'constraints': constraints
                    }
            reqList.append(req)
            if debug == True and log != None:
                log.info('Request dictionary: ' + str(req))
                
            request_start = request_end + \
                    timedelta( seconds= ( self.cadence*24.0*60.0*60.0 ) )
                    
        ur['requests'] = reqList
        ur['type'] = 'compound_request'
        self.json_request = json.dumps(ur)
        if debug == True and log != None:
            log.info(' -> Completed build of observation request')
    
    def submit_request(self, config, log=None, debug=False):
        
        params = {'username': config['user_id'] ,
                  'password': config['odin_access'], 
                  'proposal': config['proposal_id'], 
                  'request_data' : self.json_request}
        if debug == True and log != None:
            log.info( 'Observation request parameters for submission: ' + \
                                    str(params) )
        
        if str(config['simulate']).lower() == 'true':
            self.submit_status = 'SIM_add_OK'
            self.submit_response = 'Simulated'
            log.info(' -> IN SIMULATION MODE: ' + self.submit_status)
            
        else:
            url_request = urllib.urlencode(params)
            headers = {'Content-type': 'application/x-www-form-urlencoded'}
            
            secure_connect = httplib.HTTPSConnection("lcogt.net") 
            secure_connect.request("POST", "/observe/service/request/submit", 
                                               url_request, headers)
            submit_string = secure_connect.getresponse().read()	
            
            self.parse_submit_response( submit_string, log=log, debug=debug )
            secure_connect.close()
        log.info(' -> Completed obs submission')
        
    def parse_submit_response( self, submit_string, log=None, debug=False ):
        
        if debug == True and log != None:
            log.info('Request response = ' + str(submit_string) )
            
        submit_string = submit_string.replace('{','').replace('}','')
        submit_string = submit_string.replace('"','').split(',')
        
        for entry in submit_string: 
            if 'Unauthorized' in entry:
                self.submit_status = 'ERROR'
                self.submit_response = entry
            elif 'time window' in submit_string:
      		self.submit_status = 'ERROR'
                self.submit_response = entry
            else:
                try: 
                    (key,value) = entry.split(':')
                    self.submit_response = str(key) + ' = ' + str(value)
                    self.submit_status = 'add_OK'
                except ValueError:
                    try:
                        (key,value) = entry.split('=')
                        self.req_id = str(value)
                        self.submit_response = str(key) + ' = ' + str(value)
                        self.submit_status = 'add_OK'
                    except:
                        self.submit_response = str(submit_string)
                        self.submit_status = 'WARNING'
       
        if debug == True and log != None:
            log.info('Submit status: ' + str(self.submit_status))
            log.info('Submit response: ' + str(self.submit_response))
            
    def obs_record( self, config ):
        """Method to output a record, in standard format, of the current 
        observation request"""
        
        if 'OK' in str(self.submit_status):
            report = str(self.submit_status)
        else:
            report = str(self.submit_status) + ': ' + str(self.submit_response)
        
        output = ''
        for i, exptime in enumerate(self.exposure_times):
            output = output + \
                str(self.group_id) + ' ' + str(self.track_id) + ' ' + \
                str(self.req_id) + ' ' + str(self.network) + ' ' + \
                str(self.site) + ' ' + str(self.observatory) + ' ' + \
                str(self.tel).replace('a','') + ' ' + \
                str(self.instrument_class) + ' ' + str(self.name) + ' ' + \
                str(self.ra) + ' ' + str(self.dec) + \
                ' ' + str(self.filter) + ' ' + str(exptime) + ' ' + \
                str(self.exposure_counts[i]) + ' ' + str(self.exposures_taken) + \
                ' ' + str(self.group_type) + ' ' + str(self.cadence) + ' ' + \
                str(self.priority) + ' ' + self.ts_submit.strftime("%Y-%m-%dT%H:%M:%S") + ' ' + \
                self.ts_expire.strftime("%Y-%m-%dT%H:%M:%S") + ' ' + \
                str(self.tag_id) + ' ' + str(config['user_id']) + ' ' + str(config['proposal_id']) + ' ' + \
                str(self.ttl) + ' ' + str(self.twilight) + ' ' + \
                str(self.darkness) + ' ' + str(self.seeing) + ' ' + \
                str(self.focus_offset) + ' ' + str(self.rotator_angle) + ' ' +\
                str(self.autoguider) + ' ' + str(self.submit_mech) + ' ' + \
                str(self.config_type) + ' ' + str(self.req_origin) + ' ' + \
                str(report) + '\n'
        return output