'''
Created on 17 June 2017

@author: Kurliana
'''

import re
import logging.config
import time
from multiprocessing import Process, Manager

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
                if tmp_str.find("timeline 3_simple_profit:") > -1:
                    self.selected_results[-1].append(eval(tmp_str.split(":")[-1][1:]))
                    #log.info(self.selected_results[-1][0])
                if tmp_str.find("day_profit") > -1:
                    self.selected_results[-1].append(float(tmp_str.split(" ")[-1]))
                tmp_str=orig_log.readline()
        del self.selected_results[-1]
        
    def _initial_analyzer(self):
        method_list=[]
        more_less_list=[]

        for more in [0,0.1,0.2,0.3,0.5,0.7,0.9,1,1.1,1.3,1.5,1.7,1.9,2,2.5,3,3.5,5,7]:
            for less in [0.1,0.2,0.3,0.5,0.7,0.9,1,1.1,1.3,1.5,1.7,1.9,2,2.5,3,3.5,5,7,9,20,50,100,1000]:
                if more < less:
                    super_sum=1
                    day_count=0
                    total_days=1
                    for single_ind in range(len(self.selected_results)):
                        single_result =self.selected_results[single_ind]
                        if len(single_result) >1:
                            #log.info("ok %s %s" %(len(single_result),len(single_result[0])))
                            max_per_proff=-1
                            max_per_value=1
                            for day_result_ind in range(0,(len(single_result)-1),1):
                                if single_result[0][day_result_ind % len(single_result[0])][0] > more and single_result[0][day_result_ind % len(single_result[0])][0] < less:
                                    if max_per_proff < single_result[0][day_result_ind % len(single_result[0])][0]: 
                                    #log.info(single_result[day_result_ind+1])
                                        max_per_proff = single_result[0][day_result_ind % len(single_result[0])][0]
                                        max_per_value=single_result[day_result_ind+1]
                            #if max_per_value > 1:
                            #    day_count+=1
                            #else:
                            #    day_count-=1
                            #log.info("Max weight for day %s is %s" %(single_ind,max_per_proff))
                                    super_sum = super_sum+(max_per_value-1)
                                

                    log.info("Sum results %s for more %s and less %s with days %s" %(super_sum,more,less,day_count))
        return None
                
    def analize_single_method(self, method_list, more_less_list, results_dict, thread_id=0):
        #log.info("method list %s" % method_list)
        #log.info("more_less list %s" % more_less_list)
        full_results=[]
        for methods in method_list:
            for more in more_less_list:
                for less in more_less_list:
                    if more < less:
                        super_sum=[]
                        for i in range(len(self.selected_results)/40+1):
                            super_sum.append(1)
                        day_count=0
                        total_days=1
                        for single_ind in range(len(self.selected_results)):
                            single_result =self.selected_results[single_ind]
                            if len(single_result) >1:
                                max_per_proff=-1
                                max_per_value=1
                                for pair_ind in methods:#range(len(single_result)/4):
                                    if single_result[pair_ind*2] > more and single_result[pair_ind*2] < less:
                                        if single_result[pair_ind*2] > max_per_proff:
                                            #log.info(single_result[pair_ind*2])
                                            max_per_proff=single_result[pair_ind*2]
                                            max_per_value=single_result[pair_ind*2+1]
                                if max_per_proff >-1:
                                    super_sum[single_ind/40]=super_sum[single_ind/40]*max_per_value
                                    total_days+=1
                                    if max_per_value >= 1:
                                        day_count+=1
                                    else:
                                        day_count-=1
                        total_sum =1
                        for i in super_sum[:-1]:
                            if i > 0.3:
                                total_sum = total_sum*i
                            else:
                                total_sum = 0
                        total_sum = total_sum*super_sum[-1]
                        #log.info("%s %s" % (total_sum,float(day_count)/float(total_days)))
                        if total_sum > 50 and float(day_count)/float(total_days) > 0.2:
                            full_results.append([(total_sum,methods,more,less,day_count,total_days,float(day_count)/float(total_days),super_sum)])
        results_dict[thread_id]=full_results
        
    def analize_single_method_threaded(self, method_ranges = range(0,18,1)):
        method_list, more_less_list=self._initial_analyzer(method_ranges)
        full_method_list=[]
        for a in method_list:
            for b in method_list:
                for c in method_list:
                    #log.info("%s %s %s" % (a,b,c))
                    for d in method_list:
                        #for e in method_list:
                            #for f in method_list:
                                if a <= b and b <= c and c<=d: #and d<=e and e<=f:
                                    full_method_list.append([a,b,c,d])

        thread_list=[]
        manager = Manager()
        thread_counter=16
        results_dict = manager.dict()
        total_results=[]

        for thread_num in range(thread_counter-1):
            thread_list.append(Process(target=self.analize_single_method, name="t%s" % thread_num, args=[full_method_list[thread_num*len(full_method_list)/thread_counter:(thread_num+1)*len(full_method_list)/thread_counter],more_less_list,results_dict, thread_num]))
        thread_list.append(Process(target=self.analize_single_method, name="t%s" % thread_num, args=[ full_method_list[thread_num*len(full_method_list)/thread_counter:],more_less_list,results_dict, thread_counter]))
        for thread_num in range(thread_counter):
            thread_list[thread_num].start()
            
        is_alive_counter=thread_counter
        while is_alive_counter>0:
            time.sleep(1)
            is_alive_counter=0
            for thread_num in range(thread_counter):
                if thread_list[thread_num].is_alive():
                    is_alive_counter+=1
            print "alive %s" % is_alive_counter
        
        for thread_name in results_dict.keys():
            total_results+=results_dict[thread_name]   
        
        total_results.sort()
        for single_result in total_results:
            log.info(single_result)
                      
    def dump_results_to_csv(self):
        with open(self.csv_file, "w+") as dump_csv:
            for day_result in self.selected_results:
                string_to_write=""
                for single_data in day_result:
                    string_to_write +="%s:" % single_data
                dump_csv.write("%s\n" % string_to_write)


if __name__ == "__main__":
    start_timer=time.time()
    file_list=["my_app_super_full_fees_5_only_monday_3_simple_per.log",
               ]
    #for ranges in [range(0,20,1),range(10,30,1),range(10,20,1)+range(30,40,1),range(0,10,1)+range(20,30,1),range(0,10,1)+range(30,40,1)]:
    for filename in file_list:
    #log.info("Analyze file %s with ranges %s" % (filename,ranges))
        tp = TPLogAnalizer(filename,"out.csv")
        tp.simple_log_reader()
        tp._initial_analyzer()
        #tp.analize_single_method_threaded(ranges)
        #del tp
        #tp.dump_results_to_csv()
    log.info( time.time()-start_timer)    