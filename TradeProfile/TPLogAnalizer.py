'''
Created on 17 June 2017

@author: Kurliana
'''

import re
import logging.config
import time

logging.config.fileConfig('log_la.conf')
log=logging.getLogger('main')

class TPLogAnalizer():
    
    def __init__(self, log_file = "", csv_file = ""):
        self.log_file=log_file
        self.csv_file=csv_file
        self.selected_results=[[]]
        
    def simple_log_reader(self):
        with open(self.log_file, "r+") as orig_log:
            tmp_str=orig_log.readline()
            while tmp_str:
                
                if tmp_str.find("Get day profit") > -1:
                    if len(self.selected_results[-1]) > 0:
                        self.selected_results.append([])
                if tmp_str.find("Expected periods") > -1:
                    self.selected_results[-1].append(float(tmp_str.split(" ")[-1]))
                if tmp_str.find("Expected periods") > -1:
                    self.selected_results[-1].append(float(tmp_str.split(" ")[-1]))
                if tmp_str.find(": Date") > -1:
                    self.selected_results[-1].append(float(tmp_str.split(" ")[13]))
                tmp_str=orig_log.readline()
        del self.selected_results[-1]
                
    def analize_single_method(self, method_id=0):
        max_extra1=1
        max_extra2=1
        best_extra1=0
        best_extra2=0
        #for single_result in self.selected_results:
        for extra in [-5000,-3000,-1500,-1000,-500,-100,0,100,500,1000,1500,3000,5000,10000]+range(1000,3000,100):
            extra2=extra
            extra1_res=1
            extra2_res=1
            for single_method_result_ind in range(len(self.selected_results[1:])):
                single_method_result=self.selected_results[single_method_result_ind]
                if len(single_method_result) > 2:
                    if single_method_result[0] < extra2 and not single_method_result[method_id+2] == 1:
                        extra2_res=extra2_res*(single_method_result[method_id+2]-0.00)
                    if single_method_result[0]-self.selected_results[single_method_result_ind-1][0] <= extra and not single_method_result[method_id+2] == 1:
                        extra1_res=extra1_res*(single_method_result[method_id+2]-0.00)
            #log.info("Extra 1 %s: result %s,extra 2 %s: resu11lt %s" %(extra,extra1_res,extra2,extra2_res))
            if extra1_res > max_extra1:
                max_extra1=extra1_res
                best_extra1=extra
            if extra2_res > max_extra2:
                max_extra2=extra2_res
                best_extra2=extra2
        log.info("Best for method %s! extra 1 %s: result %s,extra 2 %s: result %s" %(method_id,best_extra1,max_extra1,best_extra2,max_extra2))
    
    def dump_results_to_csv(self):
        with open(self.csv_file, "w+") as dump_csv:
            for day_result in self.selected_results:
                string_to_write=""
                for single_data in day_result:
                    string_to_write +="%s," % single_data
                dump_csv.write("%s\n" % string_to_write)


if __name__ == "__main__":
    start_timer=time.time()
    tp = TPLogAnalizer("my_app.log","out.csv")
    tp.simple_log_reader()
    for method in range(40):
        tp.analize_single_method(method)
    tp.dump_results_to_csv()
    log.info( time.time()-start_timer)    