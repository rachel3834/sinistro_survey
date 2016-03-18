# -*- coding: utf-8 -*-
"""
Created on Wed Mar 16 14:58:50 2016

@author: rstreet
"""

import xml.sax
from os import path
from sys import exit

class confighandler(xml.sax.handler.ContentHandler):
    '''Class definition of the configuration handler for a generic XML config.'''
    # Initialise the function, setting the index iValue to 0 (== False)

    def __init__(self):
        self.iValue = 0
        self.mapping = {}
    
    # Start of definition of how to parse the parameter element.  
    # If the XML tag parsed is a 'parameter', initialise the data buffer and
    # store the element name attribute for later use as the dictionary key.  
    # If the XML tag is 'value', set the flag to indicate the value should be read.
    def startElement(self,name,attributes):
        if name == 'parameter':
            self.buffer = ""
            self.paramName = attributes["name"]
        elif name == 'value':
            self.iValue = 1

    # If the tag indicates this XML element holds a parameter value, add that data
    # to the buffer. 
    def characters(self, data):
        if self.iValue == 1:
            self.buffer += data

    # End of definition of how to parse the parameter element.  
    # Once the parser has the data from the 'value' tag for this parameter, 
    # add this parameter+value pair as a new element in the dictionary to be 
    # returned.  Set the self.iValue index back to 'false', ready for the next
    # parameter. 
    def endElement(self, name):
        if name == 'value':
            self.iValue = 0
            self.mapping[self.paramName] = self.buffer
 

def readxmlconfig(ConfigFile,LocalConfigs):
    '''Function to read an xml config file and return a dictionary of its contents. '''

    # Initialising execution status parameter and dictionary:
    istat = 0
    Configuration = {}
    
    # Where to find this script's configuration file
    ConfigDir = path.join(path.expanduser('~'), LocalConfigs)
    fconfig = path.join(ConfigDir,ConfigFile)
    
    # Test that we can find the ConfigFile:
    if path.isfile(fconfig) == False:
        istat = -1

    # Only continue if the file exists:
    else:
        # Declaring parameter 'parser' to hold the output of the SAX make_parser function
        # Declaring parameter 'config' to hold the output of the function ConfigHandler,
        # i.e. the returned parameter+values dictionary.
        parser = xml.sax.make_parser(  )
        config = confighandler( )

        # Tell the SAX function what function to use as to parse the config file, then
        # parse the file
        parser.setContentHandler(config)
        parser.parse(fconfig)
        Configuration = config.mapping
        
        
    # Return the fconfig.mapping dictionary:
    return istat, Configuration



###############################################
# COMMANDLINE TEST SECTION
if __name__ == '__main__':

    LocalConfigs = '/home/rstreet/Software/sinistro_survey/configs/'
    (iexec, ScriptConfig) = readxmlconfig('survey_config.xml',LocalConfigs)
    print iexec
    print ScriptConfig
    
    for item,value in ScriptConfig.items():
        print item, value
  