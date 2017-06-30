'''
Created on 06 May 2017

@author: Kurliana
'''
import time
import numpy
import requests
import shutil
import logging.config
import math
import os
import datetime
from multiprocessing import Process, Manager
from collections import Counter
#import pythoncom

logging.config.fileConfig('log.conf')
log=logging.getLogger('main')

class ProfileAnalyser():
    
    def __init__(self, tick_file = "", day_of_week=-1,logger = None):
        self.log = logger
        self.days=[]
        self.results_days=[]
        self.results_profit=[]
        self.results_procent=[]
        current_day=0
        with open(tick_file,"r+") as f:
            single_ticker = f.readline()
            while single_ticker:
                candle = single_ticker.split(",")
                candle[1]=int(candle[1])
                candle[2]=int(candle[2])
                candle[3]=int(candle[3])
                candle[4]=float(candle[4])
                candle[5]=float(candle[5])
                candle[6]=float(candle[6])
                candle[7]=float(candle[7])
                candle[8]=int(candle[8])
                if day_of_week < 0 or day_of_week == datetime.datetime(int(str(candle[2])[:4]), int(str(candle[2])[4:6]), int(str(candle[2])[6:8]), 23, 55, 55, 173504).weekday():
                    self.tickers.append(candle)
                    if not current_day == candle[2]:
                        current_day = candle[2]
                        self.days.append(current_day)
                single_ticker = f.readline()
        self.time_range=range(100000,184000,1000)
        for one_time_counter in range(len(self.time_range)-1,-1,-1):
            if self.time_range[one_time_counter] % 10000 > 5000:
                del self.time_range[one_time_counter]
        self.days.sort()

    def filter_tickers(self, tikers, begin_time=100000, end_time=120000, date_start=-1,date_end=-1,day_of_week=-1):
        filtered_tickers=[]
        for single_ticker in tikers:
            single_ticker_time=single_ticker[3]
            if single_ticker_time >= begin_time and single_ticker_time <= end_time:
                if date_start < 0 or date_start <= single_ticker[2]:
                    if date_end < 0 or date_end >= single_ticker[2]:
                        if day_of_week < 0 or day_of_week == datetime.datetime(int(str(single_ticker[2])[:4]), int(str(single_ticker[2])[4:6]), int(str(single_ticker[2])[6:8]), 23, 55, 55, 173504).weekday():
                            filtered_tickers.append(single_ticker)
                            
                        
        return filtered_tickers
    
    def group_tickers(self, tickers, group_time=3000):
        pass
    
    def combine_tickers(self, ticker1, ticker2):
        total_ticker=[]
        total_ticker+=ticker1
        total_ticker[3]=max(ticker1[3],ticker2[3])
        total_ticker[5]=max(ticker1[5],ticker2[5])
        total_ticker[6]=min(ticker1[6],ticker2[6])
        total_ticker[7]=ticker2[7]
        return total_ticker
    
    def combine_multi_tickers(self, tickers_list, start_time = -1, end_time = 200000):
        total_ticker=[]
        #high_low=[]
        min_value=200000000
        min_time=0
        max_value=0
        max_time=0
        close_time=0
     
        #print tickers_list,start_time,end_time
        for ticker in tickers_list:
            if ticker[3] > start_time and ticker[3] <= end_time:
                if ticker[5] > max_value:
                    max_value = ticker[5]
                    max_time = ticker[3]
                if ticker[6] < min_value:
                    min_value = ticker[6]
                    min_time = ticker[3]
                #high_low.append(ticker[5])
                #high_low.append(ticker[6])
                if not total_ticker:
                    total_ticker+=ticker
                close_time=ticker[7]
        if not total_ticker:
            return []
        total_ticker[3]=max_time
        total_ticker[5]=max_value
        total_ticker[6]=min_value
        total_ticker[7]=close_time
        total_ticker[8]=min_time
        total_ticker.append(0)
        
        return total_ticker
    
    def _get_list_weight_stat(self, result_list):
        result=[]
        x=[]
        for single_result in result_list:
            x.append(single_result[0])
            
        _x=numpy.array(x)    
        result.append(numpy.mean(_x))
        result.append((numpy.min(_x), numpy.max(_x)))
        result.append(numpy.std(_x))
        result.append(result[0]/result[-1])
        result.append((numpy.percentile(_x, 25), numpy.percentile(_x, 50), numpy.percentile(_x, 75)))
        log.info("List statistic: %s" % result)
        return result

    def get_list_weight_stat(self, result_list):
        pass
    
    def _find_candle_in_ranges(self, candle_ranges, begin_time = 100000, check_time=102000, start_time=102000, end_time=120000, base_ind_diff=0):
        for single_candle in candle_ranges:
            if single_candle[2+base_ind_diff] == begin_time and single_candle[3+base_ind_diff] == check_time and single_candle[4+base_ind_diff] == start_time and single_candle[5+base_ind_diff] == end_time:
                return single_candle
            
        return None
    
    def get_candle_ranges(self, selected_timelines, result_days = None):

        begin_times=[]
        check_times=[]
        start_times=[]
        end_times=[]
        trade_direct=[]
        
        for single_result in selected_timelines:
            begin_times.append(single_result[2])
            check_times.append(single_result[3])
            start_times.append(single_result[4])
            end_times.append(single_result[5])
            trade_direct.append(single_result[11])
            
        #log.info("Trade selection %s" % trade_direct)

        begin_dict=Counter(begin_times).most_common()
        check_dict=Counter(check_times).most_common()
        start_dict=Counter(start_times).most_common()
        end_dict=Counter(end_times).most_common()
        trade_dict=Counter(trade_direct).most_common()
        #print begin_dict
        
        #return [[begin_dict[0][0],check_dict[0][0],self.time_range[self.time_range.index(start_dict[0][0])+1],self.time_range[self.time_range.index(end_dict[0][0])+1],trade_dict[0][0]]]
        
        return [[begin_dict[0][0],check_dict[0][0],start_dict[0][0],end_dict[0][0],trade_dict[0][0]]]

    def _get_result_day_by_time(self, result_days, begin_time, check_time, start_time, end_time):
        for single_result in result_days:
            if single_result[2] == begin_time and single_result[3] == check_time and single_result[4] == start_time and single_result[5] == end_time:
                return single_result
        return None
    
    def get_candle_ranges_new2(self, selected_timelines, result_days = None):
        max_weight = 0
        best_timeline=[[183000,183000,183000,183000,1]]
        
        for single_result in selected_timelines:
            sum_weights=[]
            begin_times_index=self.time_range.index(single_result[2])
            check_times_index=self.time_range.index(single_result[3])
            start_times_index=self.time_range.index(single_result[4])
            end_times_index=self.time_range.index(single_result[5])
            for begin_index in [begin_times_index,begin_times_index+1]:
                for check_index in [check_times_index-1,check_times_index,check_times_index+1]:
                    for start_index in [start_times_index-1,start_times_index,start_times_index+1]:
                        for end_index in [end_times_index-1,end_times_index,end_times_index+1]:
                            begin_time = self.time_range[begin_index]
                            check_time = self.time_range[check_index]
                            start_time = self.time_range[start_index]
                            end_time = self.time_range[end_index]
                            tmp_result = self._get_result_day_by_time(result_days, begin_time, check_time, start_time, end_time)
                            if tmp_result:
                                sum_weights.append(tmp_result[0])
            sum_array = numpy.array(sum_weights)
            sum_std = numpy.std(sum_array)
            if sum_std == 0:
                sum_std=0.0000001
            single_weight = numpy.mean(numpy.array(sum_weights))/sum_std
            if single_weight >= max_weight:
                max_weight = single_weight
                best_timeline=[[single_result[2],single_result[3],single_result[4],single_result[5],single_result[11]]]
                
        return best_timeline

    def get_candle_ranges_new(self, selected_timelines, result_days = None):
        max_weight = 0
        best_timeline=[[183000,183000,183000,183000,1]]
        
        for single_result in selected_timelines:
            sum_weights=0
            begin_times_index=self.time_range.index(single_result[2])
            check_times_index=self.time_range.index(single_result[3])
            start_times_index=self.time_range.index(single_result[4])
            end_times_index=self.time_range.index(single_result[5])
            for begin_index in [begin_times_index,begin_times_index+1]:
                for check_index in [check_times_index-1,check_times_index,check_times_index+1]:
                    for start_index in [start_times_index-1,start_times_index,start_times_index+1]:
                        for end_index in [end_times_index-1,end_times_index,end_times_index+1]:
                            begin_time = self.time_range[begin_index]
                            check_time = self.time_range[check_index]
                            start_time = self.time_range[start_index]
                            end_time = self.time_range[end_index]
                            tmp_result = self._get_result_day_by_time(result_days, begin_time, check_time, start_time, end_time)
                            if tmp_result:
                                sum_weights+=tmp_result[0]
            #single_weight = numpy.mean(numpy.array(sum_weights))/numpy.std(numpy.array(sum_weights))
            if sum_weights >= max_weight:
                max_weight = sum_weights
                best_timeline=[[single_result[2],single_result[3],single_result[4],single_result[5],single_result[11]]]
                
        return best_timeline

    def is_up_direction(self, tickers_by_day, check_time=102000, direction_delta = 0):
        ticker1=self.combine_multi_tickers(tickers_by_day,-1,check_time)
        if not ticker1:
            return 0
        if (abs(ticker1[4] - ticker1[7]) > min(ticker1[4],ticker1[7])*direction_delta) and ticker1[4] < ticker1[7]:# and self.ticker1[9] > 0: #upstream
            return 1
        elif (abs(ticker1[4] - ticker1[7]) > min(ticker1[4],ticker1[7])*direction_delta) and ticker1[4] > ticker1[7]:# and self.ticker1[9] < 0:
            return -1
        else:
            return 0

    def check_direction(self, ticker2, up_direction, start_time=102000, end_time=120000, delta=0, stop_loss=0.015, take_profit=200):
        if not ticker2:
            #print "Failed to found ticker2 in case: %s, %s, %s" % (tickers_by_day, start_time, end_time)
            return None

        if up_direction > 0: #upstream
            if ticker2[6] < ticker2[4]*(1-stop_loss) and ticker2[5] > ticker2[4]*(1+take_profit):
                if ticker2[3] > ticker2[8]:
                    return (ticker2[4]*(1+take_profit))/ticker2[4]
                else:
                    return (ticker2[4]*(1-stop_loss))/ticker2[4]
            elif ticker2[6] < ticker2[4]*(1-stop_loss):
                return (ticker2[4]*(1-stop_loss))/ticker2[4]
            elif ticker2[5] > ticker2[4]*(1+take_profit):
                return (ticker2[4]*(1+take_profit))/ticker2[4]
            else:
                return ticker2[7]/ticker2[4]
        else:
            if ticker2[6] < ticker2[4]*(1-take_profit) and ticker2[5] > ticker2[4]*(1+stop_loss):
                if ticker2[3] < ticker2[8]:
                    return ticker2[4]/(ticker2[4]*(1+stop_loss))
                else:
                    return ticker2[4]/(ticker2[4]*(1-take_profit))
            elif ticker2[6] < ticker2[4]*(1-take_profit):
                return ticker2[4]/(ticker2[4]*(1-take_profit))
            elif ticker2[5] > ticker2[4]*(1+stop_loss):
                return ticker2[4]/(ticker2[4]*(1+stop_loss))
            else:
                return ticker2[4]/ticker2[7]
                
    def analyze_by_day(self, tickers, check_time=102000, start_time=102000, end_time=120000, delta=0, direction_delta = 0.001, stop_loss = 0.015, reverse_trade=1, take_profit = 200, ignore_check_limit = True):
        day_count=0
        check_diff_limit=0.02
        comission=0.02
        day_tickers=[tickers[0]]
        total_profit=0
        count_profit=1
        procn_profit=1
        list_profit=[]
        zero_days=0
        for single_ticker in tickers:
            if single_ticker[2] == day_tickers[0][2]:
                day_tickers.append(single_ticker) 
            else:
                day_count+=1
                is_up = self.is_up_direction(day_tickers,check_time,direction_delta)*reverse_trade
                if not is_up == 0:
                    ticker2=self.combine_multi_tickers(day_tickers,start_time,end_time)
                    if ticker2:
                        tmp_profit = self.check_direction(ticker2, is_up, start_time, end_time, delta, stop_loss, take_profit)-1
                        if tmp_profit:
                            if tmp_profit>0: 
                                total_profit+=1
                            else: 
                                total_profit-=1
                            if not tmp_profit == 0:
                                tmp_profit-=comission/25
                            count_profit=count_profit+tmp_profit*25
                            procn_profit=procn_profit*(1+tmp_profit*25)
                            list_profit.append(tmp_profit)
                        else:
                            list_profit.append(float(0))
                            zero_days+=1
                    else:
                        list_profit.append(float(0))
                        zero_days+=1
                else:
                    zero_days+=1
                    list_profit.append(float(0))   
                day_tickers=[single_ticker]
        day_count+=1
        is_up = self.is_up_direction(day_tickers,check_time,direction_delta)*reverse_trade
        if not is_up == 0:
            ticker2=self.combine_multi_tickers(day_tickers,start_time,end_time)
            if ticker2:
                tmp_profit = self.check_direction(ticker2, is_up, start_time, end_time, delta, stop_loss, take_profit)-1
                if tmp_profit:
                    if tmp_profit>0: 
                        total_profit+=1
                    else: 
                        total_profit-=1
                    if not tmp_profit == 0:
                        tmp_profit-=comission/25
                    count_profit=count_profit+tmp_profit*25
                    procn_profit=procn_profit*(1+tmp_profit*25)
                    list_profit.append(tmp_profit)
                else:
                    list_profit.append(float(0))
                    zero_days+=1
            else:
                list_profit.append(float(0))
                zero_days+=1
        else:
            list_profit.append(float(0))
            zero_days+=1    
        day_tickers=[single_ticker]
        return total_profit, count_profit, procn_profit, list_profit
    
    def main_analyzer(self, begin_list, check_list, start_list, end_list, date_start, date_end, stop_loss, direction_delta, results_days_dict, results_profit_dict, results_procent_dict, thread=0):
        #pythoncom.CoInitialize()
        results_days=[]
        results_profit=[]
        results_procent=[]
        take_profit=200
        delta=0
        
        #print "thread %s started: %s" % (thread,check_list)
        #for stop_loss in [0.005,0.001,0.015,0.02,0.05]:
        #    for direction_delta in [0.0015,0.005,0.01,0.02]:
        for begin in begin_list:
            for end in end_list:
                if begin < end:
                    filtered_tickers = self.filter_tickers(self.tickers, begin, end, date_start, date_end)
                    for check in check_list:
                        #print "thread %s check: %s" % (thread,check)
                        if begin < check and check < end:
                            for start in start_list:
                                if begin < check and check < start and start < end:
                                    if self.time_range.index(check) - self.time_range.index(begin) > 2 and self.time_range.index(end) - self.time_range.index(start) > 2:
                                        days,profit,procent,list_profit=self.analyze_by_day(filtered_tickers, check, start, end, delta, direction_delta, stop_loss,1,take_profit)
                                        days_rev,profit_rev,procent_rev,list_profit_rev=self.analyze_by_day(filtered_tickers, check, start, end, delta, direction_delta, stop_loss,-1,take_profit)
                                    else:
                                        days=0
                                        profit=1
                                        procent=1
                                        days_rev=0
                                        profit_rev=1
                                        procent_rev=1
                                        list_profit=[]
                                        list_profit_rev=[]
                                    results_days.append([days,begin,check,start,end,profit,procent,list_profit,stop_loss,direction_delta,1])
                                    results_profit.append([profit,begin,check,start,end,days,procent,list_profit,stop_loss,direction_delta,1])
                                    results_procent.append([procent,begin,check,start,end,days,profit,list_profit,stop_loss,direction_delta,1])
                                    results_days.append([days_rev,begin,check,start,end,profit_rev,procent_rev,list_profit_rev,stop_loss,direction_delta,-1])
                                    results_profit.append([profit_rev,begin,check,start,end,days_rev,procent_rev,list_profit_rev,stop_loss,direction_delta,-1])
                                    results_procent.append([procent_rev,begin,check,start,end,days_rev,profit_rev,list_profit_rev,stop_loss,direction_delta,-1])
        results_days_dict[thread]=results_days   
        results_profit_dict[thread]=results_profit         
        results_procent_dict[thread]=results_procent               
        #print "thread %s finished %s %s" % (thread,self.results_days,self.results_profit)
        
    def start_analyzer_threaded(self,day_start=-1,day_end=-1, threads = 16,direction_delta=0.0015,stop_loss=0.015):
        start_time_range=self.time_range#[3:]
        thread_counter=threads
        thread_list=[]
        results_days=[]
        results_profit=[]
        results_procent=[]
        manager = Manager()
        results_days_dict = manager.dict()
        results_profit_dict = manager.dict()
        results_procent_dict = manager.dict()
        for thread_num in range(thread_counter):
            thread_list.append(Process(target=self.main_analyzer, name="t%s" % thread_num, args=[[self.time_range[0]], start_time_range[thread_num*len(start_time_range)/thread_counter:(thread_num+1)*len(start_time_range)/thread_counter], self.time_range, self.time_range[:-3], day_start, day_end, stop_loss, direction_delta, results_days_dict, results_profit_dict, results_procent_dict, thread_num]))
        thread_list.append(Process(target=self.main_analyzer, name="t%s" % thread_counter, args=[[self.time_range[0]], start_time_range[len(start_time_range)/thread_counter*thread_counter:], self.time_range, self.time_range[:-3], day_start, day_end, stop_loss, direction_delta, results_days_dict, results_profit_dict, results_procent_dict, thread_counter]))
        for thread_num in range(thread_counter+1):
            thread_list[thread_num].start()
            
        is_alive_counter=thread_counter+1
        while is_alive_counter>0:
            time.sleep(1)
            is_alive_counter=0
            for thread_num in range(thread_counter+1):
                if thread_list[thread_num].is_alive():
                    is_alive_counter+=1
            print "alive %s" % is_alive_counter
        
        for thread_name in results_days_dict.keys():
            results_days+=results_days_dict[thread_name]
            results_profit+=results_profit_dict[thread_name]
            results_procent+=results_procent_dict[thread_name]
        results_days.sort()
        #log.info(results_days[0:20])
        #log.info(results_days[-22:])
        results_profit.sort()
        #log.info(results_profit[0:20])
        #log.info(results_profit[-22:])
        results_procent.sort()
        #log.info(results_procent[0:20])
        #log.info(results_procent[-22:])
        self.results_days=results_days
        self.results_profit=results_profit
        self.results_procent=results_procent
        return results_days,results_profit,results_procent
    
    def start_analyzer(self,day_start=-1,day_end=-1,direction_delta=0.0015,stop_loss=0.015):
        start_ind=0
        end_ind=0
        comission=0.02
        results_days=[]
        results_profit=[]
        results_procent=[]
        if day_start > -1:
            start_ind=self.days.index(day_start)
        if day_end > -1:
            end_ind=self.days.index(day_end)
        for single_day in self.results_days:
            days=0
            profit=1
            procent=1
            if len(single_day[7]) > 0 and not single_day[0] == 0:  
                for ind in range(start_ind,end_ind+1,1):
                    tmp_profit = single_day[7][ind]
                    if single_day[7][ind] > 0:
                        days+=1
                    elif single_day[7][ind] < 0:
                        days-=1
                        
                    profit+=tmp_profit*25
                    procent=procent*(1+tmp_profit*25)
                

                results_days.append([days]+single_day[1:5]+[profit,procent]+[single_day[7][start_ind:end_ind+1]]+single_day[8:11])     
                #results_days.append([days,single_day[1],single_day[2],single_day[3],single_day[4],profit,procent,single_day[7][start_ind:end_ind+1],stop_loss,direction_delta,single_day[10]])
                #results_profit.append([profit,single_day[1],single_day[2],single_day[3],single_day[4],days,procent,single_day[7][start_ind:end_ind+1],stop_loss,direction_delta,single_day[10]])
                #results_procent.append([procent,single_day[1],single_day[2],single_day[3],single_day[4],days,profit,single_day[7][start_ind:end_ind+1],stop_loss,direction_delta,single_day[10]])
            else:
                results_days.append(single_day)
                #results_profit.append([profit,single_day[1],single_day[2],single_day[3],single_day[4],days,procent,[],stop_loss,direction_delta,single_day[10]])
                #results_procent.append([procent,single_day[1],single_day[2],single_day[3],single_day[4],days,profit,[],stop_loss,direction_delta,single_day[10]])
        results_days.sort()
        #log.info(results_days[0:20])
        #log.info(results_days[-22:])
        #results_profit.sort()
        #log.info(results_profit[0:20])
        #log.info(results_profit[-22:])
        #results_procent.sort()
        #log.info(results_procent[0:20])
        #log.info(results_procent[-22:])
        
        return results_days
    
    def _timeline_appender(self, logic_key, result_candidate):
        timeline = []
        begin_cand_ind=self.time_range.index(result_candidate[1])
        check_cand_ind=self.time_range.index(result_candidate[2])
        start_cand_ind=self.time_range.index(result_candidate[3])
        ended_cand_ind=self.time_range.index(result_candidate[4])
        result_daily_array=numpy.array(result_candidate[7])
        result_daily_std = numpy.std(result_daily_array)
        try:
            if result_daily_std == 0:
                result_daily_std = 0.0000001
            if logic_key == "extra":
                if check_cand_ind - begin_cand_ind > 5 and check_cand_ind - begin_cand_ind < 17 and start_cand_ind - check_cand_ind > 2 and ended_cand_ind - start_cand_ind > 5:
                    timeline.append([numpy.mean(result_daily_array)/result_daily_std]+result_candidate)
            if logic_key == "extra2":
                if check_cand_ind - begin_cand_ind > 5 and check_cand_ind - begin_cand_ind < 17 and start_cand_ind - check_cand_ind > 2 and ended_cand_ind - start_cand_ind > 2:
                    timeline.append([numpy.mean(result_daily_array)/result_daily_std]+result_candidate)
            if logic_key == "best_ranges":
                if check_cand_ind - begin_cand_ind > 5 and start_cand_ind - check_cand_ind > 2 and ended_cand_ind - start_cand_ind > 2:
                    timeline.append([(float(result_candidate[0])*2)*(1/float(result_candidate[6]))]+result_candidate)
            if logic_key == "percentile2":
                if check_cand_ind - begin_cand_ind > 5 and start_cand_ind - check_cand_ind > 2 and ended_cand_ind - start_cand_ind > 2:
                    timeline.append([numpy.percentile(result_daily_array,80)]+result_candidate)
            if logic_key == "std_percentile":        
                if check_cand_ind - begin_cand_ind > 5 and start_cand_ind - check_cand_ind > 2 and ended_cand_ind - start_cand_ind > 2:
                    timeline.append([(result_candidate[0])*(result_candidate[5])*(result_daily_std)]+result_candidate)
            if logic_key == "median":                
                if check_cand_ind - begin_cand_ind > 5 and start_cand_ind - check_cand_ind > 2 and ended_cand_ind - start_cand_ind > 2:
                    timeline.append([numpy.median(result_daily_array)]+result_candidate)
            if logic_key == "percentile":
                if check_cand_ind - begin_cand_ind > 5 and start_cand_ind - check_cand_ind > 2 and ended_cand_ind - start_cand_ind > 2:
                    timeline.append([numpy.percentile(result_daily_array,75)]+result_candidate)
            if logic_key == "std":
                if check_cand_ind - begin_cand_ind > 5 and start_cand_ind - check_cand_ind > 2 and ended_cand_ind - start_cand_ind > 2:
                    timeline.append([numpy.mean(result_daily_array)/result_daily_std]+result_candidate)
            if logic_key == "std_median":
                if check_cand_ind - begin_cand_ind > 5 and start_cand_ind - check_cand_ind > 2 and ended_cand_ind - start_cand_ind > 2:
                    timeline.append([numpy.median(result_daily_array)/result_daily_std]+result_candidate)
            if logic_key == "extra_zero":
                if check_cand_ind - begin_cand_ind > 5 and check_cand_ind - begin_cand_ind < 17 and start_cand_ind - check_cand_ind > 2 and ended_cand_ind - start_cand_ind > 2:
                    timeline.append([math.sqrt(result_candidate[6])/result_candidate[6]]+result_candidate)
            if logic_key == "period_profit":
                if check_cand_ind - begin_cand_ind > 5 and start_cand_ind - check_cand_ind > 2 and ended_cand_ind - start_cand_ind > 2:
                    priod_len=len(result_candidate[7])
                    semi_period=int(math.sqrt(priod_len))
                    min_per_prof=200000000
                    for per_start in range(priod_len*2/semi_period-1):
                        semi_per_prof=1
                        for per_ind in range(semi_period):
                            semi_per_prof=semi_per_prof*(1+result_candidate[7][per_start*semi_period/2+per_ind])
                        min_per_prof=min(min_per_prof,semi_per_prof)
                    timeline.append([min_per_prof]+result_candidate)         
        except Exception as e:
            log.info("Exception: %s")
                
        return timeline        
    
    def real_trade_decisoner(self, results_days, results_profit, results_days_rev, results_profit_rev, best_range = 2, weight_multiplyer=0.6, period = 10,max_stat = -5):
        results_timeline_extra_days=[]
        results_timeline_extra_rev=[]
        results_timeline_extra2_days=[]
        results_timeline_extra2_rev=[]

        best_days=[]
        for single_result in results_days:
            if single_result[0]>0:
                best_days.append(single_result[0])

        days_limit=int(numpy.median(numpy.array(best_days[-int(len(best_days)/best_range):])))

        for result_part in results_days:
            if result_part[0] >= days_limit:
                results_timeline_extra_days+=self._timeline_appender("extra",result_part)
                results_timeline_extra2_days+=self._timeline_appender("extra2",result_part)
                    
        best_days=[]
        for single_result in results_days_rev:
            if single_result[0]>0:
                best_days.append(single_result[0])
                
        if len(best_days) > 0:
            days_limit=int(numpy.median(numpy.array(best_days[-int(len(best_days)/best_range):])))
        else:
            days_limit=2000000
        print "Days limit %s" % days_limit
   
        for result_part in results_days_rev:
            if result_part[0] >= days_limit:
                results_timeline_extra_rev+=self._timeline_appender("extra",result_part)
                results_timeline_extra2_rev+=self._timeline_appender("extra2",result_part)

        results_timeline_extra_days.sort()
        results_timeline_extra_rev.sort()
        results_timeline_extra2_days.sort()
        results_timeline_extra2_rev.sort()
        log.info("get_best_ranges_profit_std_rev results_extra_day len %s" % len(results_timeline_extra_days))
        log.info("get_best_ranges_profit_std_rev results_extra_rev len %s" % len(results_timeline_extra_rev))
        log.info("get_best_ranges_profit_std_rev results_extra2_day len %s" % len(results_timeline_extra2_days))
        log.info("get_best_ranges_profit_std_rev results_extra2_rev len %s" % len(results_timeline_extra2_rev))

        trade_dir=0

        if len(results_timeline_extra_days) > 170:
            trade_dir=1
            log.info("Good day")
        #else:
        #    log.info("Bad day")
        #    trade_dir=0
        
        return trade_dir
    
    def get_best_ranges_new_gen(self, logic_key, results_days, best_range = 2, weight_multiplyer=0.6, period = 10,max_stat = -5):
        results_timeline_days=[]

        best_days=[]
        for single_result in results_days:
            if single_result[0]>0:
                best_days.append(single_result[0])

        days_limit=int(numpy.median(numpy.array(best_days[-int(len(best_days)/best_range):])))

        for result_part in results_days:
            if result_part[0] >= days_limit:
                results_timeline_days+=self._timeline_appender(logic_key,result_part)
                    
        results_timeline_days.sort()
        log.info("%s: results_day len %s" % (logic_key,len(results_timeline_days)))

        if len(results_timeline_days) < max(abs(max_stat),period):
            log.info("No best range for %s" % logic_key)
            return None 
        #if results_timeline_days[-20][0] > 2:
            #return None
            
        if max_stat < 0:
            result_timeline=results_timeline_days[max_stat:]
        else:
            result_timeline=results_timeline_days[:max_stat]

        log.info(result_timeline)
        
        return self.get_candle_ranges(result_timeline,results_timeline_days)
    
    def get_best_ranges_double_period(self, logic_key, results_days, results_profit, period_days, period_profit, best_range = 2, weight_multiplyer=0.6, period = 10,max_stat = -5):
        results_timeline_days=[]
        results_timeline_period=[]

        best_days=[]
        for single_result in results_days:
            if single_result[0]>0:
                best_days.append(single_result[0])

        days_limit=int(numpy.median(numpy.array(best_days[-int(len(best_days)/best_range):])))

        for result_part in results_days:
            if result_part[0] >= days_limit:
                results_timeline_days+=self._timeline_appender(logic_key,result_part)
                    
        results_timeline_days.sort()
        log.info("%s: results_day len %s" % (logic_key,len(results_timeline_days)))

        if len(results_timeline_days) < max(abs(max_stat),period):
            log.info("No best range for %s" % logic_key)
            return None 
       
        if max_stat < 0:
            result_timeline=results_timeline_days[:-max_stat]
        else:
            result_timeline=results_timeline_days[-max_stat:]

        for single_result in result_timeline:
            find_candle = self._find_candle_in_ranges(period_days,single_result[2],single_result[3],single_result[4],single_result[5],-1)
            if find_candle:
                results_timeline_period+=self._timeline_appender(logic_key,find_candle)
                    
        results_timeline_period.sort()
        
        
        result_to_return = [[183000, 183000, 183000, 183000,1]]
        max_diff=-1
        for single_result in result_timeline:
            weight_coeff=single_result[0]/results_timeline_days[-1][0]
            find_candle = self._find_candle_in_ranges(results_timeline_period,single_result[2],single_result[3],single_result[4],single_result[5])
            if find_candle and max_diff < find_candle[0]:#/results_timeline_period[-1][0]:
                max_diff = find_candle[0]#/results_timeline_period[-1][0]
                result_to_return = [[find_candle[2],find_candle[3],find_candle[4],find_candle[5],find_candle[6]]]
        
        return result_to_return

    def get_ranges_by_dayweek(self,curr_date):
        day_of_week = datetime.datetime(int(str(curr_date)[:4]), int(str(curr_date)[4:6]), int(str(curr_date)[6:8]), 23, 55, 55, 173504).weekday()
        """day_ranges={0:[100000, 110000, 115000, 142000,1],
                    1:[100000, 145000, 151000, 155000,-1],
                    2:[100000, 122000, 123000, 143000,1],
                    3:[100000, 134000, 135000, 145000,1],
                    4:[100000, 142000, 144000, 161000,1],
                    5:[183000, 183000, 183000, 183000,1],
                    6:[183000, 183000, 183000, 183000,1]}"""
        day_ranges={0:[100000, 120000, 133000, 170000,1],
                    1:[100000, 110000, 130000, 165000,1],
                    2:[100000, 151000, 170000, 173000,1],
                    3:[100000, 113000, 131000, 154000,1],
                    4:[100000, 124000, 133000, 152000,1],
                    5:[183000, 183000, 183000, 183000,1],
                    6:[183000, 183000, 183000, 183000,1]}
        """day_ranges={0:[100000, 130000, 132000, 170000,1],
                    1:[100000, 105000, 130000, 165000,1],
                    2:[183000, 183000, 183000, 183000,1],
                    3:[183000, 183000, 183000, 183000,1],
                    4:[100000, 124000, 132000, 165000,1],
                    5:[183000, 183000, 183000, 183000,1],
                    6:[183000, 183000, 183000, 183000,1]}"""

        return [day_ranges[day_of_week]]
    
    def get_ranges_by_dayweek_new(self,curr_date):
        day_of_week = datetime.datetime(int(str(curr_date)[:4]), int(str(curr_date)[4:6]), int(str(curr_date)[6:8]), 23, 55, 55, 173504).weekday()
        day_ranges={0:[100000, 112000, 155000, 180000,1],
                    1:[100000, 113000, 123000, 141000,1],
                    2:[100000, 112000, 141000, 172000,-1],
                    3:[100000, 105000, 112000, 141000,-1],
                    4:[100000, 113000, 121000, 163000,1],
                    5:[183000, 183000, 183000, 183000,1],
                    6:[183000, 183000, 183000, 183000,1]}
        return [day_ranges[day_of_week]]

    def get_day_profit_old(self, curr_date, period = 30,period2 = 30,simulate_trade=True):
        used_ranges=[]
        ranges_counter=0
        profit_delta=0.25
        procent_delta=1.25
        loss=0.015
        delta=0.0015
        trade_dir=1
        day_profit_list=[]
        day_count_list=[]
        day_procent_list=[]
        day_list_profit_list=[]
        trade_direction_list=[]
        results_days=[]
        results_profit=[]
        results_procent=[]
        results_days_rev=[]
        results_profit_rev=[]
        results_procent_rev=[]
        results_days_dir=[]
        results_profit_dir=[]
        results_procent_dir=[]
        thread_period_dict={"0":2,"1":2,"2":2,"3":2,"5":3,"10":4,"15":5,"30":6,"60":7,"180":12}
        if "%s" % period in thread_period_dict.keys():
            thread_count = thread_period_dict["%s" % period]
        else:
            thread_count = 16
        curr_date_pos=self.days.index(curr_date)
        log.info("Get day profit %s" % curr_date)
        if curr_date_pos <= period or curr_date_pos <= period2*5:
            return [-1], [-1], [-1], []
        
        day_of_week = datetime.datetime(int(str(curr_date)[:4]), int(str(curr_date)[4:6]), int(str(curr_date)[6:8]), 23, 55, 55, 173504).weekday()
        if day_of_week > 4:
            log.info("Let's skip weekend day %s" % curr_date)
            return [-1], [-1], [-1], []
        
        if not self.results_days:
            self.start_analyzer_threaded(-1,-1,16,delta,loss)
        
        period_day_tickers = self.filter_tickers(self.tickers, 100000,184000,self.days[curr_date_pos-period-1],self.days[curr_date_pos-1])
        results_days_all = self.start_analyzer(self.days[curr_date_pos-period-1],self.days[curr_date_pos-1],delta,loss)
        #reserv_tickers=self.tickers
        #self.tickers = pa.filter_tickers(self.tickers, 100000,184000,self.days[curr_date_pos-period2*5-1],self.days[curr_date_pos-1],day_of_week)
        #results_days2,results_profit2,results_procent2 = self.start_analyzer_threaded(-1,-1,thread_period_dict[str(period2)],delta,loss)
        #self.tickers=reserv_tickers
        success_day_counter=0
        reverse_day_counter=0
        for result in results_days_all:
            if result[10] == 1:
                results_days_dir.append(result)
                if result[6] > 1:
                    success_day_counter+=1
            else:
                if result[6] > 1:
                    reverse_day_counter+=1
                results_days_rev.append(result)
        log.info("Success periods %s" % success_day_counter)
        log.info("Reverse periods %s" % reverse_day_counter)
        """for result in results_profit_all:
            if result[10] == 1:
                results_profit_dir.append(result)
            else:
                results_profit_rev.append(result)
        for result in results_procent_all:
            if result[10] == 1:
                results_procent_dir.append(result)
            else:
                results_procent_rev.append(result)"""
                
        #trade_dir = self.real_trade_decisoner(results_days_dir,results_profit_dir,results_days_rev,results_profit_rev,8,0.6,period,-5)
        """best_ranges_dir = self.get_best_ranges_new_gen("best_ranges",results_days_dir, results_profit_dir,8,0.6,period,-5)[0]
        best_ranges_rev = self.get_best_ranges_new_gen("best_ranges",results_days_rev, results_profit_rev,8,0.6,period,-5)[0]
        if not best_ranges_rev:
            trade_dir=-1
            results_days=results_days_rev
            results_profit=results_profit_rev
            results_procent=results_procent_rev
        elif not best_ranges_dir:
            trade_dir=1
            results_days=results_days_dir
            results_profit=results_profit_dir
            results_procent=results_procent_dir
        else:
            day_profit_dir, day_count_dir, day_procent_dir, day_list_profit_dir = self.analyze_by_day(period_day_tickers, best_ranges_dir[1], best_ranges_dir[2], best_ranges_dir[3], 0, 0.0015, 0.015, 1, 200, True)
            day_profit_rev, day_count_rev, day_procent_rev, day_list_profit_rev = self.analyze_by_day(period_day_tickers, best_ranges_rev[1], best_ranges_rev[2], best_ranges_rev[3], 0, 0.0015, 0.015, -1, 200, True)
            if day_procent_dir > day_procent_rev:
                trade_dir=-1
                results_days=results_days_rev
                results_profit=results_profit_rev
                results_procent=results_procent_rev
            else:
                trade_dir=1"""

        if success_day_counter > 0:#day_of_week in [0,1,2,3,4]:
            results_days=results_days_dir
        #elif reverse_day_counter > 4500:
        #    results_days=results_days_rev
        #    results_profit=results_profit_rev
        #    results_procent=results_procent_rev
        else:
            return  [-1], [-1], [-1], []
        #else:
        #    return  [-1], [-1], [-1]
       
        best_ranges1 = self.get_best_ranges_new_gen("median",results_days, 8,0.6,period,-5)
        best_ranges2 = self.get_best_ranges_new_gen("extra2",results_days, 8,0.6,30,-5)
        best_ranges3 = self.get_best_ranges_new_gen("percentile",results_days, 8,0.6,period,-5)
        best_ranges4 = self.get_best_ranges_new_gen("std",results_days, 8,0.6,period,-5)
        best_ranges5 = self.get_best_ranges_new_gen("std_median",results_days, 8,0.6,period,-5)
        best_ranges6 = self.get_best_ranges_new_gen("extra",results_days, 8,0.6,10,-5)
        best_ranges7 = self.get_best_ranges_new_gen("best_ranges",results_days,8,0.6,period,-5)
        best_ranges8 = self.get_best_ranges_new_gen("period_profit",results_days, 8,0.6,period,-5)
        best_ranges9 = self.get_ranges_by_dayweek(curr_date)
        best_ranges10 = self.get_ranges_by_dayweek(curr_date)
        if not best_ranges1 or not best_ranges2 or not best_ranges3 or not best_ranges4 or not best_ranges5 or not best_ranges6 or not best_ranges7 or not best_ranges8:
            log.info("No some best ranges, lets skip")
            return [-1], [-1], [-1], []
        best_ranges = best_ranges1 + best_ranges2 + best_ranges3 + best_ranges4 + best_ranges5 + best_ranges6 + best_ranges7 + best_ranges8+best_ranges9+best_ranges10

        for best_range in best_ranges:
            used_ranges.append(best_range)
            ranges_counter+=1
            begin_time,check_time,start_time,end_time = best_range[0], best_range[1], best_range[2], best_range[3]
            day_profit, day_count, day_procent, day_list_profit = self.analyze_by_day(period_day_tickers, check_time, start_time, end_time, 0, 0.0015, loss, best_range[4], 200, True)
            log.info("Period %s: day_profit %s, day_count %s, day_procent %s" % (ranges_counter,day_profit, day_count, day_procent))
            log.info("Begin %s, check %s, start %s, end %s,trade direct %s" % (begin_time,check_time,start_time,end_time,best_range[4]))
            if simulate_trade:
                day_tickers = self.filter_tickers(self.tickers, begin_time,end_time,curr_date,curr_date)
                day_profit, day_count, day_procent, day_list_profit = self.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, 0.0015, loss, best_range[4], 200, True)
                day_profit_list.append(day_profit)
                day_count_list.append(day_count)
                log.info("day_profit %s %s, day_count %s, day_procent %s" % (ranges_counter,day_profit, day_count, day_procent))
                trade_direction_list.append(trade_dir)
            else:
                day_profit_list.append(0)
                day_count_list.append(1)
                log.info("day_profit %s, day_count %s, day_procent %s" % (0, 1, 1))
                trade_direction_list.append(1)

        for best_range in best_ranges:
            used_ranges.append(best_range)
            ranges_counter+=1
            begin_time,check_time,start_time,end_time = best_range[0], best_range[1], best_range[2], best_range[3]
            day_profit, day_count, day_procent, day_list_profit = self.analyze_by_day(period_day_tickers, check_time, start_time, end_time, 0, 0.01, loss, best_range[4],  200, True)
            log.info("Period %s: day_profit %s, day_count %s, day_procent %s" % (ranges_counter,day_profit, day_count, day_procent))
            log.info("Begin %s, check %s, start %s, end %s,trade direct %s" % (begin_time,check_time,start_time,end_time,best_range[4]))
            if simulate_trade:
                day_tickers = self.filter_tickers(self.tickers, begin_time,end_time,curr_date,curr_date)
                day_profit, day_count, day_procent, day_list_profit = self.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, 0.01, loss, best_range[4],  200, True)
                day_profit_list.append(day_profit)
                day_count_list.append(day_count)
                log.info("day_profit %s %s, day_count %s, day_procent %s" % (ranges_counter,day_profit, day_count, day_procent))
                trade_direction_list.append(trade_dir)
            else:
                day_profit_list.append(0)
                day_count_list.append(1)
                log.info("day_profit %s, day_count %s, day_procent %s" % (0, 1, 1))
                trade_direction_list.append(1)

        """results_days=results_days_rev
        best_ranges1 = self.get_best_ranges_new_gen("median",results_days, 8,0.6,period,-5)
        best_ranges2 = self.get_best_ranges_new_gen("extra2",results_days, 8,0.6,30,-5)
        best_ranges3 = self.get_best_ranges_new_gen("percentile",results_days, 8,0.6,period,-5)
        best_ranges4 = self.get_best_ranges_new_gen("std",results_days, 8,0.6,period,-5)
        best_ranges5 = self.get_best_ranges_new_gen("std_median",results_days, 8,0.6,period,-5)
        best_ranges6 = self.get_best_ranges_new_gen("extra",results_days, 8,0.6,10,-5)
        best_ranges7 = self.get_best_ranges_new_gen("best_ranges",results_days,8,0.6,period,-5)
        best_ranges8 = self.get_best_ranges_new_gen("period_profit",results_days, 8,0.6,period,-5)
        best_ranges9 = self.get_ranges_by_dayweek(curr_date)
        best_ranges10 = self.get_ranges_by_dayweek(curr_date)
        if not best_ranges1 or not best_ranges2 or not best_ranges3 or not best_ranges4 or not best_ranges5 or not best_ranges6 or not best_ranges7 or not best_ranges8:
            log.info("No some best ranges, lets skip")
            return [-1], [-1], [-1]
        best_ranges = best_ranges1 + best_ranges2 + best_ranges3 + best_ranges4 + best_ranges5 + best_ranges6 + best_ranges7 + best_ranges8+best_ranges9+best_ranges10"""

        #if reverse_day_counter < 3000:
        #    return day_profit_list, day_count_list,trade_direction_list
                
        """best_ranges1 = self.get_best_ranges_double_period("median",results_days2,results_profit2,results_days, results_profit_rev,8,0.6,period,-15)
        best_ranges2 = self.get_best_ranges_double_period("extra2",results_days2,results_profit2,results_days, results_profit,8,0.6,30,-15)
        best_ranges3 = self.get_best_ranges_double_period("percentile",results_days2,results_profit2,results_days, results_profit_rev,8,0.6,period,-15)
        best_ranges4 = self.get_best_ranges_double_period("std",results_days2,results_profit2,results_days, results_profit,8,0.6,period,-15)
        best_ranges5 = self.get_best_ranges_double_period("std_median",results_days2,results_profit2,results_days, results_profit,8,0.6,period,-15)
        best_ranges6 = self.get_best_ranges_double_period("extra",results_days2,results_profit2,results_days, results_profit,8,0.6,10,-15)
        best_ranges7 = self.get_best_ranges_double_period("best_ranges",results_days2,results_profit2,results_days, results_profit_rev,8,0.6,period,-15)
        best_ranges8 = self.get_best_ranges_double_period("period_profit",results_days2,results_profit2,results_days, results_profit_rev,8,0.6,period,-15)
        best_ranges9 = self.get_ranges_by_dayweek(curr_date)
        best_ranges10 = self.get_ranges_by_dayweek_new(curr_date)
        if not best_ranges1 or not best_ranges2 or not best_ranges3 or not best_ranges4 or not best_ranges5 or not best_ranges6 or not best_ranges7 or not best_ranges8:
            log.info("No some best ranges, lets skip")
            return [-1], [-1], [-1]
        best_ranges = best_ranges1 + best_ranges2 + best_ranges3 + best_ranges4 + best_ranges5 + best_ranges6 + best_ranges7 + best_ranges8 +best_ranges9+best_ranges10
        log.info(best_ranges)"""

        for best_range in best_ranges:
            used_ranges.append(best_range)
            ranges_counter+=1
            begin_time,check_time,start_time,end_time = best_range[0], best_range[1], best_range[2], best_range[3]
            day_profit, day_count, day_procent, day_list_profit = self.analyze_by_day(period_day_tickers, check_time, start_time, end_time, 0, 0.0015, 0.01, best_range[4], 200, True)
            log.info("Period %s: day_profit %s, day_count %s, day_procent %s" % (ranges_counter,day_profit, day_count, day_procent))
            log.info("Begin %s, check %s, start %s, end %s,trade direct %s" % (begin_time,check_time,start_time,end_time,best_range[4]))
            if simulate_trade:
                day_tickers = self.filter_tickers(self.tickers, begin_time,end_time,curr_date,curr_date)
                day_profit, day_count, day_procent, day_list_profit = self.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, 0.0015, 0.01, best_range[4], 200, True)
                day_profit_list.append(day_profit)
                day_count_list.append(day_count)
                log.info("day_profit %s %s, day_count %s, day_procent %s" % (ranges_counter,day_profit, day_count, day_procent))
                trade_direction_list.append(trade_dir)
            else:
                day_profit_list.append(0)
                day_count_list.append(1)
                log.info("day_profit %s, day_count %s, day_procent %s" % (0, 1, 1))
                trade_direction_list.append(1)


        """
        best_ranges1 = self.get_best_ranges_double_period("median",results_days2,results_profit2,results_days, results_profit_rev,8,0.6,period,-15)
        best_ranges2 = self.get_best_ranges_double_period("extra2",results_days2,results_profit2,results_days, results_profit,8,0.6,30,-15)
        best_ranges3 = self.get_best_ranges_double_period("percentile",results_days2,results_profit2,results_days, results_profit_rev,8,0.6,period,-15)
        best_ranges4 = self.get_best_ranges_double_period("std",results_days2,results_profit2,results_days, results_profit,8,0.6,period,-15)
        best_ranges5 = self.get_best_ranges_double_period("std_median",results_days2,results_profit2,results_days, results_profit,8,0.6,period,-15)
        best_ranges6 = self.get_best_ranges_double_period("extra",results_days2,results_profit2,results_days, results_profit,8,0.6,10,-15)
        best_ranges7 = self.get_best_ranges_double_period("best_ranges",results_days2,results_profit2,results_days, results_profit_rev,8,0.6,period,-15)
        best_ranges8 = self.get_best_ranges_double_period("period_profit",results_days2,results_profit2,results_days, results_profit_rev,8,0.6,period,-15)
        best_ranges9 = self.get_ranges_by_dayweek(curr_date)
        best_ranges10 = self.get_ranges_by_dayweek_new(curr_date)
        
        if not best_ranges1 or not best_ranges2 or not best_ranges3 or not best_ranges4 or not best_ranges5 or not best_ranges6 or not best_ranges7:
            log.info("No some best ranges, lets skip")
            return [-1], [-1], [-1]
        best_ranges = best_ranges1 + best_ranges2 + best_ranges3 + best_ranges4 + best_ranges5 + best_ranges6 + best_ranges7 + best_ranges8+best_ranges9+best_ranges10
"""
        for best_range in best_ranges:
            used_ranges.append(best_range)
            ranges_counter+=1
            begin_time,check_time,start_time,end_time = best_range[0], best_range[1], best_range[2], best_range[3]
            day_profit, day_count, day_procent, day_list_profit = self.analyze_by_day(period_day_tickers, check_time, start_time, end_time, 0, 0.01,0.01, best_range[4], 200, True)
            log.info("Period %s: day_profit %s, day_count %s, day_procent %s" % (ranges_counter,day_profit, day_count, day_procent))
            log.info("Begin %s, check %s, start %s, end %s,trade direct %s" % (begin_time,check_time,start_time,end_time,best_range[4]))
            if simulate_trade:
                day_tickers = self.filter_tickers(self.tickers, begin_time,end_time,curr_date,curr_date)
                day_profit, day_count, day_procent, day_list_profit = self.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, 0.01, 0.01, best_range[4], 200, True)
                day_profit_list.append(day_profit)
                day_count_list.append(day_count)
                log.info("day_profit %s %s, day_count %s, day_procent %s" % (ranges_counter,day_profit, day_count, day_procent))
                trade_direction_list.append(trade_dir)
            else:
                day_profit_list.append(0)
                day_count_list.append(1)
                log.info("day_profit %s, day_count %s, day_procent %s" % (0, 1, 1))
                trade_direction_list.append(1)

        
        return day_profit_list, day_count_list,trade_direction_list,used_ranges
           
    def robot(self, date_start=-1, period = 10, period2 = 0):
        self.tickers = self.filter_tickers(self.tickers, 100000,184000,-1,-1)
        if date_start > 0:
            date_start_index=self.days.index(date_start)
            self.days=self.days[-len(self.days)+date_start_index-max(period,period2*5)-1:]
        total_profit_list=[]
        total_profit = []
        total_count = []
        total_procent_profit = []
        total_extra_profit = []
        changer_period=120
        for single_day in self.days:
            day_analyze_time_start=time.time()
            day_profit_list, day_count_list,trade_direction_list,used_ranges=self.get_day_profit_old(single_day, period,period2)
            if len(total_profit_list) > changer_period:           
                accumul_prof=1
                best_prof=0
                if len(day_count_list) > 18: 
                    for saved_prof_ind in range(min(len(day_count_list),39)):
                        method_per_prof=1
                        for prev_profit in range(changer_period):
                            method_per_prof=method_per_prof*total_profit_list[-prev_profit-1][saved_prof_ind]
                        log.info("TotalProfit method %s: %s with day profit %s" % (saved_prof_ind,method_per_prof,day_count_list[saved_prof_ind]))
                        if method_per_prof > best_prof:
                            #if method_per_prof > 1.9 and saved_prof_ind in [0,2]:
                            #    accumul_prof = 1
                            #    break
                            if saved_prof_ind in [4, 9, 10, 15, 17] and method_per_prof < 7: #[0,8,10,14]
                                best_prof = method_per_prof
                                accumul_prof = day_count_list[saved_prof_ind]
                day_count_list.append(accumul_prof)
                day_profit_list.append(0) 
                if accumul_prof > 1:
                    day_profit_list[-1] = 1
                elif accumul_prof < 1:
                    day_profit_list[-1] = -1
                trade_direction_list.append(1)  
            if len(total_profit) <= len(day_profit_list) and len(day_profit_list) > 1:
                for check_func in range(len(day_profit_list)):
                    day_count=day_count_list[check_func]
                    day_profit=day_profit_list[check_func]
                    trade_direction=trade_direction_list[check_func]
                    if len(total_profit)<check_func+1:
                        total_profit.append(1)
                        total_count.append(0)
                        total_procent_profit.append(1)
                        total_extra_profit.append(1)
                    if day_count > 0:
                        #if trade_direction > 0:
                            log.info("Date %s, profit %s, count %s" % (single_day, day_profit, day_count))
                            total_profit[check_func]=total_profit[check_func]+(day_count-1)
                            total_procent_profit[check_func] = total_procent_profit[check_func]*day_count
                            total_count[check_func]+=day_profit
                            total_extra_profit[check_func]=max(total_extra_profit[check_func]-round(total_extra_profit[check_func]/2)+round(total_extra_profit[check_func]/2)*day_count,1)
                        #elif trade_direction < 0:
                        #    log.info("Date %s, profit %s, count %s" % (single_day, -day_profit, day_count))
                            #total_profit=total_profit+(day_count-1)
                            #total_procent_profit = total_procent_profit*day_count
                        #    total_profit[check_func]=total_profit[check_func]+(1/day_count-1)
                        #    total_procent_profit[check_func] = total_procent_profit[check_func]*(1/day_count)
                        #    total_count[check_func]-=day_profit
                    log.info("Method %s!!! Total profit %s, total procent profit %s, total count %s, total extra profit %s,time %s" % (check_func,total_profit[check_func],total_procent_profit[check_func],total_count[check_func], total_extra_profit[check_func], time.time()-day_analyze_time_start))
                if len(day_profit_list) > 1:
                    total_profit_list.append(day_count_list)
        return total_profit, total_count

if __name__ == "__main__":
    start_timer=time.time()
    pa = ProfileAnalyser("TATN_150101_170506.txt")
    #begin_time,check_time,start_time,end_time = 100000, 111000, 130000, 173000
    #day_tickers = pa.filter_tickers(pa.tickers, 100000,184000,20150105,20150705)
    #print pa.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, 0.01,0.015,1)
    #day_tickers = pa.filter_tickers(pa.tickers, 100000,184000,20150705,20160104)
    #print pa.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, 0.01,0.015,1)
    #day_tickers = pa.filter_tickers(pa.tickers, 100000,184000,20160104,20160705)
    #print pa.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, 0.01,0.015,1)
    #day_tickers = pa.filter_tickers(pa.tickers, 100000,184000,20160705,20170104)
    #print pa.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, 0.01,0.015,1)
    #day_tickers = pa.filter_tickers(pa.tickers, 100000,184000,20170104,20170506)
    #print pa.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, 0.01,0.015,1)
    #print pa.analyze_by_day(day_tickers, 113000, 121000, 141000, 0, 0.0005,0.015,1)
    #print pa.analyze_by_day(day_tickers, 115000, 121000, 141000, 0, 0.0005,0.015,1)
    #print pa.analyze_by_day(day_tickers, 114000, 115000, 141000, 0, 0.0005,0.015,1)
    #print pa.analyze_by_day(day_tickers, 114000, 122000, 141000, 0, 0.0005,0.015,1)
    #print pa.analyze_by_day(day_tickers, 114000, 121000, 140000, 0, 0.0005,0.015,1)
    #print pa.analyze_by_day(day_tickers, 114000, 121000, 135000, 0, 0.0005,0.015,1)
    #print pa.analyze_by_day(day_tickers, 125000, 141000, 165000, 0, 0.0015)
    #print pa.analyze_by_day(pa.tickers, 111000, 143000, 175000, 0, 0.0015)
    #print pa.analyze_by_day(pa.tickers, 111000, 144000, 175000, 0, 0.0015)
    #print pa.analyze_by_day(pa.tickers, 111000, 142000, 175000, 0, 0.0015)
    log.info(pa.robot(20150105,30))
    #print pa.start_analyzer_threaded()
    #day_tickers = pa.filter_tickers(pa.tickers, 100000,184000)
    #log.info( pa.analyze_by_day(day_tickers, 111000, 143000, 180000, 0, 0.0015))
    #dates=[20150105,20150401,20150701,20151001,20160101,20160401,20160701,20161001,20170101,20170505]
    #for sdi in range(len(dates)-2):
    """for weekday in [-1]:
        for delta in [0.0015]:
            for loss in [0.015]:
                log.info("delta %s, stop %s" % (delta, loss))
                pa = ProfileAnalyser("TATN_150101_170506.txt")
                day_tickers = pa.filter_tickers(pa.tickers, 100000,184000,-1,-1,weekday)
                pa.tickers = day_tickers
                results_days=[]
                results_profit=[]
                results_procent=[]
                results_days_rev=[]
                results_profit_rev=[]
                results_procent_rev=[]
                results_days_dir=[]
                results_profit_dir=[]
                results_procent_dir=[]
                #spec_dates_list=[20150105,20150705,20160104,20160705,20170104,20170506,20170506]
                spec_dates_list=[-1,-1]
                for tmpdate in range(len(spec_dates_list)-1):
                    results_days=[]
                    results_profit=[]
                    results_procent=[]
                    results_days_rev=[]
                    results_profit_rev=[]
                    results_procent_rev=[]
                    results_days_dir=[]
                    results_profit_dir=[]
                    results_procent_dir=[]
                    results_days_all, results_profit_all, results_procent = pa.start_analyzer_threaded(day_start=spec_dates_list[tmpdate],day_end=spec_dates_list[tmpdate+1],threads=16,direction_delta=delta,stop_loss=loss)
                    for result in results_days_all:
                        if result[10] == 1:
                            results_days_dir.append(result)
                        else:
                            results_days_rev.append(result)
                    for result in results_profit_all:
                        if result[10] == 1:
                            results_profit_dir.append(result)
                        else:
                            results_profit_rev.append(result)
                    for logic_key in ["std","extra","extra2","median","std_median","period_profit","percentile"]:
                        ranges = pa.get_best_ranges_new_gen(logic_key,results_days_dir, 8,0.6,5,-5)
                        if ranges:
                            begin_time,check_time,start_time,end_time,trade = ranges[0]
                            log.info("Time %s" % logic_key)
                            log.info( "%s, %s, %s, %s" % (begin_time,check_time,start_time,end_time))
                            log.info( "Result %s" % logic_key)
                            day_tickers = pa.filter_tickers(pa.tickers, 100000,184000,spec_dates_list[tmpdate],spec_dates_list[tmpdate+1])
                            log.info( pa.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, delta, loss, 1))
                            day_tickers = pa.filter_tickers(pa.tickers, 100000,184000,20150105,20150705)
                            log.info(pa.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, delta, loss,1))
                            day_tickers = pa.filter_tickers(pa.tickers, 100000,184000,20150705,20160104)
                            log.info(pa.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, delta, loss,1))
                            day_tickers = pa.filter_tickers(pa.tickers, 100000,184000,20160104,20160705)
                            log.info(pa.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, delta, loss,1))
                            day_tickers = pa.filter_tickers(pa.tickers, 100000,184000,20160705,20170104)
                            log.info(pa.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, delta, loss,1))
                            day_tickers = pa.filter_tickers(pa.tickers, 100000,184000,20170104,20170506)
                            log.info(pa.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, delta, loss,1))
                del pa
                del day_tickers
                del results_days
                del results_profit
                del results_procent
                del results_days_rev
                del results_profit_rev
                del results_procent_rev
                del results_days_dir
                del results_profit_dir
                del results_procent_dir"""
 
    log.info( time.time()-start_timer)