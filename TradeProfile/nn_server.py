'''
Created on 6 Jan 2018

Main server for neuron network analyzer 

@author: Kurliana
'''

import logging.config
import os
import time

logging.config.fileConfig('log_server.conf')
log=logging.getLogger('main')

from nn_main_trader import NNTrader

class NNServer():
    
    def __init__(self, monitoring_path = "C:\\Just2Trade Client",file_name_template = "tickers_"):
        self.monitoring_path=monitoring_path
        self.file_name_template=file_name_template
        self.file_mon_dict={}
        self.nnt = NNTrader(model_path = "nn_trade_test_model4.h5", init_model = False)

    def update_single_file_direction(self, full_file_path):
        try:
            self.nnt.prepare_data(full_file_path,"world")
            result_direction = self.nnt.get_last_direction()
        except Exception as e:
            log.error("NNServer: exception during get last direction for file %s - %s" % (full_file_path,e))
            result_direction = -2
            
        if not result_direction[-1] == 1 and not result_direction[-1] == 0 and not result_direction[-1] == -1:
            log.error("NNServer: Failed to get direction for file %s" % full_file_path)
        else:
            trade_file_name=full_file_path.replace(self.file_name_template,"trade_")
            try:
                if result_direction[-1]*result_direction[-2] == 1:
                    with open(trade_file_name,'w') as trade_file:
                        trade_file.write("%d" % result_direction[-1])
                log.info("NNServer: direction %s was written to file %s" % (result_direction[-1],trade_file_name))
            except Exception as e:
                log.error("NNServer: Exception during write file %s - %s" % (trade_file_name,e))
            
    def search_for_ticker_files(self):
        for single_file in os.listdir(self.monitoring_path):
            if single_file.find(self.file_name_template) == 0:
                if single_file in self.file_mon_dict.keys():
                    if not self.file_mon_dict[single_file] == os.path.getmtime(self.monitoring_path+"\\"+single_file):
                        log.info("NNServer: found file %s with updated modification time %s" % (single_file,os.path.getmtime(self.monitoring_path+"\\"+single_file)))
                        self.update_single_file_direction(self.monitoring_path+"\\"+single_file)
                log.debug("NNServer: Update file %s modification time %s" % (single_file,os.path.getmtime(self.monitoring_path+"\\"+single_file)))
                self.file_mon_dict[single_file]=os.path.getmtime(self.monitoring_path+"\\"+single_file)     
                
    def main_cycle(self):
        while True:
            try:
                log.debug("NNServer: Start new main cycle")
                self.search_for_ticker_files()
                log.debug("NNServer: Stop main cycle, sleeping")
                time.sleep(30)
            except Exception as e:
                log.error("NNServer: Exception in main cycle %s" % e)
                    
if __name__ == "__main__":
    nns = NNServer()
    nns.main_cycle()
