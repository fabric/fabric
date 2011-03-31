import logging                                                                                                                                                  
from logging.handlers import *                                                                                                                                  
logger = logging.getLogger("fabric")                                                                                                                 
logger.setLevel(logging.DEBUG)                                                                                                                                  
consolelogger = logging.StreamHandler()                                                                                                                         
consolelogger.setLevel(logging.DEBUG)                                                                                                                           
logger.addHandler(consolelogger)  
debuglogger = logging.FileHandler('fabric.debug_log', mode='w')                                                                                                
debugFormat = logging.Formatter('%(asctime)s lineno=%(lineno)d %(levelname)s %(module)s %(funcName)s %(message)s')                                              
debuglogger.setFormatter(debugFormat)                                                                                                                           
debuglogger.setLevel(logging.DEBUG)                                                                                                                             
logger.addHandler(debuglogger)  
