'''
Created on 06 May 2017

@author: Kurliana
'''
import time
import numpy
import logging
import logging.config
import ConfigParser
from multiprocessing import Process, Manager
from collections import Counter
#import pythoncom

logging.config.fileConfig('log.conf')
log=logging.getLogger('main')

class ProfileAnalyser():
    
    def __init__(self, tick_file = ""):
        self.tickers=[]
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
                self.tickers.append(candle)
                single_ticker = f.readline()
        self.time_range=range(100000,184000,1000)
        for one_time_counter in range(len(self.time_range)-1,-1,-1):
            if self.time_range[one_time_counter] % 10000 > 5000:
                del self.time_range[one_time_counter]

    def filter_tickers(self, tikers, begin_time=100000, end_time=120000, date_start=-1,date_end=-1):
        filtered_tickers=[]
        self.days=[]
        current_day=0
        for single_ticker in tikers:
            if not current_day == single_ticker[2]:
                current_day = single_ticker[2]
                self.days.append(current_day)
            single_ticker_time=single_ticker[3]
            if single_ticker_time >= begin_time and single_ticker_time <= end_time:
                if date_start < 0 or date_start <= single_ticker[2]:
                    if date_end < 0 or date_end >= single_ticker[2]:
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
                else:
                    total_ticker[7]=ticker[7]
        if not total_ticker:
            return []
        total_ticker[3]=max_time
        total_ticker[5]=max_value
        total_ticker[6]=min_value
        total_ticker[8]=min_time
        
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
    

    def is_up_direction(self, tickers_by_day, check_time=102000, direction_delta = 0):
        self.ticker1=self.combine_multi_tickers(tickers_by_day,-1,check_time)
        if (direction_delta == 0 or abs(self.ticker1[4] - self.ticker1[7]) > min(self.ticker1[4],self.ticker1[7])*direction_delta) and self.ticker1[4] < self.ticker1[7]: #upstream
            return 1 
        elif (direction_delta == 0 or abs(self.ticker1[4] - self.ticker1[7]) > min(self.ticker1[4],self.ticker1[7])*direction_delta) and self.ticker1[4] > self.ticker1[7]:
            return -1
#        elif not direction_delta == 0 and float(self.ticker1[4]) < float(self.ticker1[7]) and float(self.ticker1[4]) + direction_delta > float(self.ticker1[7]): #upstream
#            return 1
#        elif not direction_delta == 0 and float(self.ticker1[4]) > float(self.ticker1[7]) and float(self.ticker1[4]) - direction_delta < float(self.ticker1[7]): #upstream
#            return -1
        else:
            #print "Null %s" % (self.ticker1)
            return 0

    def check_direction_old(self, tickers_by_day, up_direction, start_time=102000, end_time=120000, delta=0, stop_loss=0.015):
        self.ticker2=self.combine_multi_tickers(tickers_by_day,start_time,end_time)
        if not self.ticker2:
            #print "Failed to found self.ticker2 in case: %s, %s, %s" % (tickers_by_day, start_time, end_time)
            return None
        if not delta == 0:
            if up_direction > 0: #upstream
                if self.ticker2[4]+delta > self.ticker2[5]:
                    return self.ticker2[7] - self.ticker2[4]
                else:
                    return delta
            else:
                if self.ticker2[4]-delta < self.ticker2[6]:
                    return self.ticker2[4] - self.ticker2[7]
                else:
                    return delta
        else:
            if up_direction > 0: #upstream
                if self.ticker2[6] < self.ticker2[4]*(1-stop_loss):
                    return (self.ticker2[4]*(1-stop_loss))/self.ticker2[4]
                else:
                    return self.ticker2[7]/self.ticker2[4]
            else:
                if self.ticker2[5] > self.ticker2[4]*(1+stop_loss):
                    return self.ticker2[4]/(self.ticker2[4]*(1+stop_loss))
                else:
                    return self.ticker2[4]/self.ticker2[7]
    
    def check_direction(self, tickers_by_day, up_direction, start_time=102000, end_time=120000, delta=0, stop_loss=0.015, take_profit=200):
        self.ticker2=self.combine_multi_tickers(tickers_by_day,start_time,end_time)
        if not self.ticker2:
            #print "Failed to found self.ticker2 in case: %s, %s, %s" % (tickers_by_day, start_time, end_time)
            return None
        if not delta == 0:
            if up_direction > 0: #upstream
                if self.ticker2[4]+delta > self.ticker2[5]:
                    return self.ticker2[7] - self.ticker2[4]
                else:
                    return delta
            else:
                if self.ticker2[4]-delta < self.ticker2[6]:
                    return self.ticker2[4] - self.ticker2[7]
                else:
                    return delta
        else:
            if up_direction > 0: #upstream
                if self.ticker2[6] < self.ticker2[4]*(1-stop_loss) and self.ticker2[5] > self.ticker2[4]*(1+take_profit):
                    if self.ticker2[3] > self.ticker2[8]:
                        return (self.ticker2[4]*(1+take_profit))/self.ticker2[4]
                    else:
                        return (self.ticker2[4]*(1-stop_loss))/self.ticker2[4]
                elif self.ticker2[6] < self.ticker2[4]*(1-stop_loss):
                    return (self.ticker2[4]*(1-stop_loss))/self.ticker2[4]
                elif self.ticker2[5] > self.ticker2[4]*(1+take_profit):
                    return (self.ticker2[4]*(1+take_profit))/self.ticker2[4]
                else:
                    return self.ticker2[7]/self.ticker2[4]
            else:
                if self.ticker2[6] < self.ticker2[4]*(1-take_profit) and self.ticker2[5] > self.ticker2[4]*(1+stop_loss):
                    if self.ticker2[3] < self.ticker2[8]:
                        return self.ticker2[4]/(self.ticker2[4]*(1+stop_loss))
                    else:
                        return self.ticker2[4]/(self.ticker2[4]*(1-take_profit))
                elif self.ticker2[6] < self.ticker2[4]*(1-take_profit):
                    return self.ticker2[4]/(self.ticker2[4]*(1-take_profit))
                elif self.ticker2[5] > self.ticker2[4]*(1+stop_loss):
                    return self.ticker2[4]/(self.ticker2[4]*(1+stop_loss))
                else:
                    return self.ticker2[4]/self.ticker2[7]

    def analyze_by_day(self, tickers, check_time=102000, start_time=102000, end_time=120000, delta=0, direction_delta = 0.001, stop_loss = 0.015, reverse_trade=1, take_profit = 200):
        day_count=0
        day_tickers=[tickers[0]]
        day_stat=[]
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
                    tmp_profit = self.check_direction(day_tickers, is_up, start_time, end_time, delta, stop_loss, take_profit)
                    #print single_ticker[2], tmp_profit, count_profit, procn_profit
                    if tmp_profit:
                        if tmp_profit>1: 
                            total_profit+=1
                        else: 
                            total_profit-=1
                        count_profit=count_profit+(tmp_profit-1)*25
                        procn_profit=procn_profit*(1+(tmp_profit-1)*25)
                        list_profit.append(tmp_profit-1)
                    else:
                        zero_days+=1
                else:
                    zero_days+=1    
                day_tickers=[single_ticker]
        day_count+=1
        is_up = self.is_up_direction(day_tickers,check_time,direction_delta)*reverse_trade
        if not is_up == 0:
            tmp_profit = self.check_direction(day_tickers, is_up, start_time, end_time, delta, stop_loss, take_profit)
            #print single_ticker[2], tmp_profit, count_profit, procn_profit
            if tmp_profit:
                if tmp_profit>1: 
                    total_profit+=1
                else: 
                    total_profit-=1
                #day_stat.append([tmp_profit,single_ticker[2],is_up])
                count_profit=count_profit+(tmp_profit-1)*25
                procn_profit=procn_profit*(1+(tmp_profit-1)*25)
                list_profit.append(tmp_profit-1)
            else:
                zero_days+=1
        else:
            zero_days+=1    
        day_tickers=[single_ticker]
        #print single_ticker[2], tmp_profit, count_profit, procn_profit
        #day_stat.sort()
        #print day_stat
        #print day_stat[-12:]
        #print zero_days
        return total_profit, count_profit, procn_profit, list_profit
    
    def main_analyzer(self, begin_list, check_list, start_list, end_list, date_start, date_end, delta, direction_delta, results_days_dict, results_profit_dict, results_procent_dict, thread=0):
        #pythoncom.CoInitialize()
        results_days=[]
        results_profit=[]
        results_procent=[]
        stop_loss=0.015
        take_profit=200
        
        #print "thread %s started: %s" % (thread,check_list)
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
        
    def start_analyzer_threaded(self,day_start=-1,day_end=-1, threads = 16):
        start_time_range=self.time_range#[3:]
        thread_counter=threads
        delta=0
        direction_delta=0.0015
        thread_list=[]
        results_days=[]
        results_profit=[]
        results_procent=[]
        manager = Manager()
        results_days_dict = manager.dict()
        results_profit_dict = manager.dict()
        results_procent_dict = manager.dict()
        for thread_num in range(thread_counter):
            thread_list.append(Process(target=self.main_analyzer, name="t%s" % thread_num, args=[[self.time_range[0]], start_time_range[thread_num*len(start_time_range)/thread_counter:(thread_num+1)*len(start_time_range)/thread_counter], self.time_range, self.time_range[:-3], day_start, day_end, delta, direction_delta, results_days_dict, results_profit_dict, results_procent_dict, thread_num]))
        thread_list.append(Process(target=self.main_analyzer, name="t%s" % thread_counter, args=[[self.time_range[0]], start_time_range[len(start_time_range)/thread_counter*thread_counter:], self.time_range, self.time_range[:-3], day_start, day_end, delta, direction_delta, results_days_dict, results_profit_dict, results_procent_dict, thread_counter]))
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
        
        for thread_name in results_days_dict.keys():
            results_days+=results_days_dict[thread_name]
            results_profit+=results_profit_dict[thread_name]
            results_procent+=results_procent_dict[thread_name]
        results_days.sort()
        log.info(results_days[0:20])
        log.info(results_days[-22:-1])
        results_profit.sort()
        log.info(results_profit[0:20])
        log.info(results_profit[-22:-1])
        results_procent.sort()
        log.info(results_procent[0:20])
        log.info(results_procent[-22:-1])
        return results_days,results_profit,results_procent
    
    def get_best_ranges_weight(self, results_days, results_profit, best_range = 2, weight_multiplyer=0.6):
        best_days=[]
        best_prof=[]
        for single_result in results_days:
            if single_result[0]>0:
                best_days.append(single_result[0])
        for single_result in results_profit:
            if single_result[0]>1:
                best_prof.append(single_result[0])
        days_limit=int(numpy.median(numpy.array(best_days[-int(len(best_days)/best_range):])))
        profit_limit=int(numpy.median(numpy.array(best_prof[-int(len(best_prof)/best_range):])))
        print "Days limit %s" % days_limit
        print "Prof limit %s" % profit_limit
        results_timeline=[]
        results_timeline_days=[]
        results_timeline_prof=[]
        for candle in self.time_range:
            candle_weight=0
            for result_part in results_days:
                if result_part[0] >= days_limit and result_part[5] >= profit_limit:
                    if candle < result_part[2]:
                        candle_weight-=1
                    if candle > result_part[3] and candle < result_part[4]:
                        candle_weight+=1
            results_timeline_days.append([candle,candle_weight])
        results_timeline_days.sort()
        for candle in self.time_range:
            candle_weight=0
            for result_part in results_profit:
                if result_part[0] >= profit_limit and result_part[5] >= days_limit:
                    if candle <= result_part[2]:
                        candle_weight-=1
                    if candle >= result_part[3] and candle <= result_part[4]:
                        candle_weight+=1
            results_timeline_prof.append([candle,candle_weight])
        results_timeline_prof.sort()
        print results_timeline_days
        print results_timeline_prof
        for candle_id in range(len(results_timeline_prof)):
            results_timeline.append([results_timeline_prof[candle_id][0],results_timeline_prof[candle_id][1]+results_timeline_days[candle_id][1]])
        print results_timeline
        max_weight=0
        min_weight=0
        begin_time=""
        check_time=self.time_range[0]
        start_time=""
        end_time=self.time_range[0]
        for candle_id in range(len(results_timeline)):
            if results_timeline[candle_id][1]<min_weight:
                min_weight=results_timeline[candle_id][1]
            if results_timeline[candle_id][1]>max_weight:
                max_weight=results_timeline[candle_id][1]
                
        for candle_id in range(len(results_timeline)):
            if results_timeline[candle_id][1]<min_weight*weight_multiplyer:
                if begin_time == "":
                    begin_time = results_timeline[candle_id][0]
                check_time=results_timeline[candle_id][0]
            if results_timeline[candle_id][1]>max_weight*weight_multiplyer:
                if start_time == "":
                    start_time = results_timeline[candle_id][0]
                end_time=results_timeline[candle_id][0]
                        
        return begin_time,check_time,start_time,end_time
    
    def get_best_ranges_new_weight(self, results_days, results_profit, best_range = 2, weight_multiplyer=0.6, period = 10):
        best_days=[]
        best_prof=[]
        """for single_result in results_days:
            if single_result[1] == 100000 and single_result[2] == 111000 and single_result[3] == 143000 and single_result[4] == 180000:
                log.info("!!!!14301800 %s" % single_result)
                
        for single_result in results_days:
            if single_result[0]>0:
                best_days.append(single_result[0])
        for single_result in results_profit:
            if single_result[0]>1:
                best_prof.append(single_result[0])
        days_limit=int(numpy.median(numpy.array(best_days[-int(len(best_days)/best_range):])))
        profit_limit=int(numpy.median(numpy.array(best_prof[-int(len(best_prof)/best_range):])))
        print "Days limit %s" % days_limit
        print "Prof limit %s" % profit_limit
        results_timeline=[]"""
        results_timeline_days=[]
        results_timeline_prof=[]
        for result_part in results_days:
            #if result_part[0] >= days_limit and result_part[5] >= profit_limit:
            results_timeline_days.append([result_part[0]*(result_part[5]-1)]+result_part)
                #results_timeline_days.append([result_part[0]]+result_part)
        results_timeline_days.sort()
        results_timeline_days=results_timeline_days[-10:]
        log.info(results_timeline_days)
        candle_weight_check={}
        candle_weight_trade={}
        
        for candle_id in self.time_range:
            candle_weight_check["%s" % candle_id]=0
            candle_weight_trade["%s" % candle_id]=0
        
        max_weight_check=0
        max_weight_trade=0

        for single_result in results_timeline_days:
            for candle_time in candle_weight_check.keys():
                if int(candle_time) > single_result[2] and int(candle_time) <= single_result[3]:
                    candle_weight_check[candle_time]-=single_result[0]
                    if single_result[0] > max_weight_check:
                        max_weight_check=single_result[0]
                if int(candle_time) > single_result[4] and int(candle_time) <= single_result[5]:
                    candle_weight_trade[candle_time]+=single_result[0]
                    if candle_weight_trade[candle_time] > max_weight_trade:
                        max_weight_trade=candle_weight_trade[candle_time]
        begin_time=self.time_range[0]
        check_time=self.time_range[0]
        start_time=0
        end_time=self.time_range[0]

        for candle_id in self.time_range:
            if candle_weight_check["%s" % candle_id]<=-max_weight_check*weight_multiplyer:
                #if begin_time == 0:
                #    begin_time = candle_id
                check_time=candle_id
            if candle_weight_trade["%s" % candle_id]>=max_weight_trade*weight_multiplyer:
                if start_time == 0:
                    start_time = candle_id
                end_time=candle_id
                
        return [[begin_time,check_time,start_time,end_time,1]]

    def get_best_ranges(self, results_days, results_profit, best_range = 2, weight_multiplyer=0.6, period = 10, max_stat = -5):
        best_days=[]
        best_prof=[]
        max_prof_proc=0
        if max_stat<0:
            trade_sign=1
        else:
            trade_sign=-1
        """for single_result in results_days:
            if single_result[1] == 100000 and single_result[2] == 111000 and single_result[3] == 143000 and single_result[4] == 180000:
                log.info("!!!!14301800 %s" % single_result)"""

        for single_result in results_days:
            if single_result[0]>0:
                best_days.append(single_result[0])
        for single_result in results_profit:
            if single_result[0]>1:
                best_prof.append(single_result[0])
            if trade_sign>0:
                if single_result[6] > max_prof_proc:
                    max_prof_proc = single_result[6]
            else:
                if 1/single_result[6] > max_prof_proc:
                    max_prof_proc = 1/single_result[6]
        days_limit=int(numpy.median(numpy.array(best_days[-int(len(best_days)/best_range):])))
        profit_limit=int(numpy.median(numpy.array(best_prof[-int(len(best_prof)/best_range):])))
        print "Days limit %s" % days_limit
        print "Prof limit %s" % profit_limit
        results_timeline=[]
        results_timeline_days=[]
        results_timeline_prof=[]
        for result_part in results_days:
            if max_stat<=0:
                #if result_part[0] >= days_limit and result_part[5] >= profit_limit:
                if self.time_range.index(result_part[2]) - self.time_range.index(result_part[1]) > 5 and self.time_range.index(result_part[3]) - self.time_range.index(result_part[2]) > 2 and self.time_range.index(result_part[4]) - self.time_range.index(result_part[3]) > 2:
                    results_timeline_days.append([(float(result_part[0])*2/period)*(float(result_part[6])/max_prof_proc)]+result_part)
            else:
                if self.time_range.index(result_part[2]) - self.time_range.index(result_part[1]) > 5 and self.time_range.index(result_part[3]) - self.time_range.index(result_part[2]) > 2 and self.time_range.index(result_part[4]) - self.time_range.index(result_part[3]) > 2:
                    results_timeline_days.append([(float(-result_part[0])*2/period)*(1/float(result_part[6])/max_prof_proc)]+result_part)
            #results_timeline_days.append([result_part[0]]+result_part)
        results_timeline_days.sort()
        if len(results_timeline_days) < 1:
            log.info("No best range for get_best_ranges")
            return None 
        log.info(results_timeline_days[-20:])
        self.get_list_weight_stat(results_timeline_days[-20:])
        begin_times=[]
        check_times=[]
        start_times=[]
        end_times=[]
        trade_direct=[]
        selected_timelines=results_timeline_days[-abs(max_stat):]
        for single_result in selected_timelines:
            begin_times.append(single_result[2])
            check_times.append(single_result[3])
            start_times.append(single_result[4])
            end_times.append(single_result[5])
            trade_direct.append(single_result[6]/abs(single_result[6]))

        begin_dict=Counter(begin_times).most_common()
        check_dict=Counter(check_times).most_common()
        start_dict=Counter(start_times).most_common()
        end_dict=Counter(end_times).most_common()
        trade_dict=Counter(trade_direct).most_common()
        #print begin_dict
                        
        return [[begin_dict[0][0],check_dict[0][0],start_dict[0][0],end_dict[0][0],trade_dict[0][0]]]
        #return [[results_timeline_days[-1][2],results_timeline_days[-1][3],results_timeline_days[-1][4],results_timeline_days[-1][5],results_timeline_days[-1][1]]]
        #return results_timeline_days[0][2],results_timeline_days[0][3],results_timeline_days[0][4],results_timeline_days[0][5]
        
    def get_best_ranges_profit_percentile2(self, results_days, results_profit, best_range = 2, weight_multiplyer=0.6, period = 10, max_stat=-5):
        best_days=[]
        best_prof=[]
        """for single_result in results_days:
            if single_result[1] == 100000 and single_result[2] == 111000 and single_result[3] == 143000 and single_result[4] == 180000:
                log.info("!!!!14301800 %s" % single_result)"""

        for single_result in results_days:
            if single_result[0]>0:
                best_days.append(single_result[0])
        for single_result in results_profit:
            if single_result[0]>1:
                best_prof.append(single_result[0])
        days_limit=int(numpy.median(numpy.array(best_days[-int(len(best_days)/best_range):])))
        profit_limit=int(numpy.median(numpy.array(best_prof[-int(len(best_prof)/best_range):])))
        print "Days limit %s" % days_limit
        print "Prof limit %s" % profit_limit
        results_timeline=[]
        results_timeline_days=[]
        results_timeline_prof=[]
        for result_part in results_days:
            #print result_part[7]
            if result_part[0] >= days_limit and result_part[5] >= profit_limit:
                if self.time_range.index(result_part[2]) - self.time_range.index(result_part[1]) > 5 and self.time_range.index(result_part[3]) - self.time_range.index(result_part[2]) > 2 and self.time_range.index(result_part[4]) - self.time_range.index(result_part[3]) > 2:
                    results_timeline_days.append([numpy.percentile(numpy.array(result_part[7]),80)]+result_part)
            #results_timeline_days.append([result_part[0]]+result_part)
        results_timeline_days.sort()
        if len(results_timeline_days) < 1:
            return None 
        log.info(results_timeline_days[20:])
        self.get_list_weight_stat(results_timeline_days[-20:])
        begin_times=[]
        check_times=[]
        start_times=[]
        end_times=[]
        trade_direct=[]
        
        for single_result in results_timeline_days[max_stat:]:
            begin_times.append(single_result[2])
            check_times.append(single_result[3])
            start_times.append(single_result[4])
            end_times.append(single_result[5])
            trade_direct.append(single_result[6]/abs(single_result[6]))

        begin_dict=Counter(begin_times).most_common()
        check_dict=Counter(check_times).most_common()
        start_dict=Counter(start_times).most_common()
        end_dict=Counter(end_times).most_common()
        trade_dict=Counter(trade_direct).most_common()
        #print begin_dict
                        
        return [[begin_dict[0][0],check_dict[0][0],start_dict[0][0],end_dict[0][0],trade_dict[0][0]]]
    
    def get_best_ranges_profit_std_percentile(self, results_days, results_profit, best_range = 2, weight_multiplyer=0.6, period = 10 ,max_stat=-5):
        best_days=[]
        best_prof=[]
        if max_stat<0:
            trade_sign=1
        else:
            trade_sign=-1
        """for single_result in results_days:
            if single_result[1] == 100000 and single_result[2] == 111000 and single_result[3] == 143000 and single_result[4] == 180000:
                log.info("!!!!14301800 %s" % single_result)"""

        for single_result in results_days:
            if single_result[0]>0:
                best_days.append(single_result[0])
        for single_result in results_profit:
            if single_result[0]>1:
                best_prof.append(single_result[0])
        days_limit=int(numpy.median(numpy.array(best_days[-int(len(best_days)/best_range):])))
        profit_limit=int(numpy.median(numpy.array(best_prof[-int(len(best_prof)/best_range):])))
        print "Days limit %s" % days_limit
        print "Prof limit %s" % profit_limit
        results_timeline=[]
        results_timeline_days=[]
        results_timeline_prof=[]
        for result_part in results_days:
            if trade_sign<0:
                for result_day_index in range(len(result_part[7])-1):
                    result_part[7][result_day_index]=-result_part[7][result_day_index]
            #if result_part[0] >= days_limit and result_part[5] >= profit_limit:
            if self.time_range.index(result_part[2]) - self.time_range.index(result_part[1]) > 5 and self.time_range.index(result_part[3]) - self.time_range.index(result_part[2]) > 2 and self.time_range.index(result_part[4]) - self.time_range.index(result_part[3]) > 2:
                results_timeline_days.append([(float(result_part[6]))*numpy.median(numpy.array(result_part[7]))/numpy.std(numpy.array(result_part[7]))]+result_part)
            #results_timeline_days.append([result_part[0]]+result_part)
        results_timeline_days.sort()
        if len(results_timeline_days) < -max_stat:
            log.info("No best range for get_best_ranges_profit_std_percentile")
            return None 
        log.info(results_timeline_days[max_stat:])
        self.get_list_weight_stat(results_timeline_days[-20:])
        begin_times=[]
        check_times=[]
        start_times=[]
        end_times=[]
        trade_direct=[]
        
        for single_result in results_timeline_days[max_stat:]:
            begin_times.append(single_result[2])
            check_times.append(single_result[3])
            start_times.append(single_result[4])
            end_times.append(single_result[5])
            trade_direct.append(single_result[6]/abs(single_result[6]))

        begin_dict=Counter(begin_times).most_common()
        check_dict=Counter(check_times).most_common()
        start_dict=Counter(start_times).most_common()
        end_dict=Counter(end_times).most_common()
        trade_dict=Counter(trade_direct).most_common()
        #print begin_dict
                        
        return [[begin_dict[0][0],check_dict[0][0],start_dict[0][0],end_dict[0][0],trade_dict[0][0]]]
    
    def get_best_ranges_profit_median(self, results_days, results_profit, best_range = 2, weight_multiplyer=0.6, period = 10, max_stat = -5):
        best_days=[]
        best_prof=[]
        if max_stat<0:
            trade_sign=1
        else:
            trade_sign=-1
        """for single_result in results_days:
            if single_result[1] == 100000 and single_result[2] == 111000 and single_result[3] == 143000 and single_result[4] == 180000:
                log.info("!!!!14301800 %s" % single_result)"""

        for single_result in results_days:
            if single_result[0]>0:
                best_days.append(single_result[0])
        for single_result in results_profit:
            if single_result[0]>1:
                best_prof.append(single_result[0])
        days_limit=int(numpy.median(numpy.array(best_days[-int(len(best_days)/best_range):])))
        profit_limit=int(numpy.median(numpy.array(best_prof[-int(len(best_prof)/best_range):])))
        print "Days limit %s" % days_limit
        print "Prof limit %s" % profit_limit
        results_timeline=[]
        results_timeline_days=[]
        results_timeline_prof=[]
        for result_part in results_days:
            if trade_sign<0:
                for result_day_index in range(len(result_part[7])-1):
                    result_part[7][result_day_index]=-result_part[7][result_day_index]
            
            if result_part[0] >= days_limit and result_part[5] >= profit_limit:
                if self.time_range.index(result_part[2]) - self.time_range.index(result_part[1]) > 5 and self.time_range.index(result_part[3]) - self.time_range.index(result_part[2]) > 2 and self.time_range.index(result_part[4]) - self.time_range.index(result_part[3]) > 2:
                    results_timeline_days.append([numpy.median(numpy.array(result_part[7]))]+result_part)
            #results_timeline_days.append([result_part[0]]+result_part)
        results_timeline_days.sort()
        if len(results_timeline_days) < 1:
            return None 
        log.info(results_timeline_days[-20:])
        self.get_list_weight_stat(results_timeline_days[-20:])
        begin_times=[]
        check_times=[]
        start_times=[]
        end_times=[]
        trade_direct=[]
        if max_stat <= 0:
            selected_timelines=results_timeline_days[max_stat:]
        else:
            selected_timelines=results_timeline_days[:max_stat]
        for single_result in selected_timelines:
            begin_times.append(single_result[2])
            check_times.append(single_result[3])
            start_times.append(single_result[4])
            end_times.append(single_result[5])
            trade_direct.append(single_result[6]/abs(single_result[6]))

        begin_dict=Counter(begin_times).most_common()
        check_dict=Counter(check_times).most_common()
        start_dict=Counter(start_times).most_common()
        end_dict=Counter(end_times).most_common()
        trade_dict=Counter(trade_direct).most_common()
        #print begin_dict
                        
        return [[begin_dict[0][0],check_dict[0][0],start_dict[0][0],end_dict[0][0],trade_dict[0][0]]]

    def get_best_ranges_profit_percentile(self, results_days, results_profit, best_range = 2, weight_multiplyer=0.6, period = 10, max_stat = -5):
        best_days=[]
        best_prof=[]
        result_days_list=[]
        if max_stat<0:
            trade_sign=1
        else:
            trade_sign=-1
        """for single_result in results_days:
            if single_result[1] == 100000 and single_result[2] == 111000 and single_result[3] == 143000 and single_result[4] == 180000:
                log.info("!!!!14301800 %s" % single_result)"""

        for single_result in results_days:
            if single_result[0]>0:
                best_days.append(single_result[0])
        for single_result in results_profit:
            if single_result[0]>1:
                best_prof.append(single_result[0])
        days_limit=int(numpy.median(numpy.array(best_days[-int(len(best_days)/best_range):])))
        profit_limit=int(numpy.median(numpy.array(best_prof[-int(len(best_prof)/best_range):])))
        print "Days limit %s" % days_limit
        print "Prof limit %s" % profit_limit
        results_timeline=[]
        results_timeline_days=[]
        results_timeline_prof=[]

        for result_part in results_days:
            #print result_part[7]
            #if result_part[0] >= days_limit and result_part[5] >= profit_limit:
            if trade_sign<0:
                for result_day_index in range(len(result_part[7])-1):
                    result_part[7][result_day_index]=-result_part[7][result_day_index]
            #if result_part[0] >= days_limit and result_part[5] >= profit_limit:
            if self.time_range.index(result_part[2]) - self.time_range.index(result_part[1]) > 5 and self.time_range.index(result_part[3]) - self.time_range.index(result_part[2]) > 2 and self.time_range.index(result_part[4]) - self.time_range.index(result_part[3]) > 2:
                results_timeline_days.append([numpy.percentile(numpy.array(result_part[7]),75)]+result_part)
            #results_timeline_days.append([result_part[0]]+result_part)
        results_timeline_days.sort()
        if len(results_timeline_days) < 1:
            log.info("No best range for get_best_ranges_profit_percentile")
            return None 
        log.info(results_timeline_days[-20:])
        self.get_list_weight_stat(results_timeline_days[-20:])
        begin_times=[]
        check_times=[]
        start_times=[]
        end_times=[]
        trade_direct=[]
        
        selected_timelines=results_timeline_days[-abs(max_stat):]
        for single_result in selected_timelines:
            begin_times.append(single_result[2])
            check_times.append(single_result[3])
            start_times.append(single_result[4])
            end_times.append(single_result[5])
            trade_direct.append(single_result[6]/abs(single_result[6]))

        begin_dict=Counter(begin_times).most_common()
        check_dict=Counter(check_times).most_common()
        start_dict=Counter(start_times).most_common()
        end_dict=Counter(end_times).most_common()
        trade_dict=Counter(trade_direct).most_common()
        #print begin_dict
                        
        return [[begin_dict[0][0],check_dict[0][0],start_dict[0][0],end_dict[0][0],trade_dict[0][0]]]

    def get_best_ranges_profit_std(self, results_days, results_profit, best_range = 2, weight_multiplyer=0.6, period = 10,max_stat = -5):
        best_days=[]
        best_prof=[]
        if max_stat<0:
            trade_sign=1
        else:
            trade_sign=-1
        """for single_result in results_days:
            if single_result[1] == 100000 and single_result[2] == 111000 and single_result[3] == 143000 and single_result[4] == 180000:
                log.info("!!!!14301800 %s" % single_result)"""
        for single_result in results_days:
            if single_result[0]*trade_sign>0:
                best_days.append(single_result[0])
        #for single_result in results_profit:
        #    if single_result[0]>1 and trade_sign > 0:
        #        best_prof.append(single_result[0])
        #    elif single_result[0]<1 and trade_sign < 0:
        #        best_prof.append(single_result[0])
        days_limit=int(numpy.median(numpy.array(best_days[-int(len(best_days)/best_range):])))
        #profit_limit=int(numpy.median(numpy.array(best_prof[-int(len(best_prof)/best_range):])))
        print "Days limit %s" % days_limit
        #print "Prof limit %s" % profit_limit
        results_timeline=[]
        results_timeline_days=[]
        results_timeline_prof=[]
        for result_part in results_days:
            if trade_sign<0:
                for result_day_index in range(len(result_part[7])-1):
                    result_part[7][result_day_index]=-result_part[7][result_day_index]
            #print result_part[7]
            if result_part[0] >= days_limit:# and result_part[5] >= profit_limit:
                if self.time_range.index(result_part[2]) - self.time_range.index(result_part[1]) > 5 and self.time_range.index(result_part[3]) - self.time_range.index(result_part[2]) > 2 and self.time_range.index(result_part[4]) - self.time_range.index(result_part[3]) > 2:
                    results_timeline_days.append([numpy.mean(numpy.array(result_part[7]))/numpy.std(numpy.array(result_part[7]))]+result_part)
            #results_timeline_days.append([result_part[0]]+result_part)
        results_timeline_days.sort()
        if len(results_timeline_days) < 20:
            log.info("No best range for get_best_ranges_profit_std")
            return None 
        #if results_timeline_days[-20][0] > 2:
            #return None
        log.info(results_timeline_days[-20:])
        self.get_list_weight_stat(results_timeline_days[-20:])
        begin_times=[]
        check_times=[]
        start_times=[]
        end_times=[]
        trade_direct=[]
         
        for single_result in results_timeline_days[-abs(max_stat):]:
            begin_times.append(single_result[2])
            check_times.append(single_result[3])
            start_times.append(single_result[4])
            end_times.append(single_result[5])
            trade_direct.append(single_result[6]/abs(single_result[6]))

        begin_dict=Counter(begin_times).most_common()
        check_dict=Counter(check_times).most_common()
        start_dict=Counter(start_times).most_common()
        end_dict=Counter(end_times).most_common()
        trade_dict=Counter(trade_direct).most_common()
        #print begin_dict
                                
        return [[begin_dict[0][0],check_dict[0][0],start_dict[0][0],end_dict[0][0],trade_dict[0][0]]]
    
    def get_best_ranges_profit_std_median(self, results_days, results_profit, best_range = 2, weight_multiplyer=0.6, period = 10 ,max_stat=-5):
        best_days=[]
        best_prof=[]
        if max_stat<0:
            trade_sign=1
        else:
            trade_sign=-1
        """for single_result in results_days:
            if single_result[1] == 100000 and single_result[2] == 111000 and single_result[3] == 143000 and single_result[4] == 180000:
                log.info("!!!!14301800 %s" % single_result)"""
        for single_result in results_days:
            if single_result[0]*trade_sign>0:
                best_days.append(single_result[0]*trade_sign)
        best_days.sort()
        #for single_result in results_profit:
        #    if single_result[0]>1 and trade_sign > 0:
        #        best_prof.append(single_result[0])
        #    elif single_result[0]<1 and trade_sign < 0:
        #        best_prof.append(single_result[0])
        days_limit=int(numpy.median(numpy.array(best_days[-int(len(best_days)/best_range):])))
        #profit_limit=int(numpy.median(numpy.array(best_prof[-int(len(best_prof)/best_range):])))
        print "Days limit %s" % days_limit
        #print "Prof limit %s" % profit_limit
        results_timeline=[]
        results_timeline_days=[]
        results_timeline_prof=[]
        for result_part in results_days:
            if trade_sign<0:
                for result_day_index in range(len(result_part[7])-1):
                    result_part[7][result_day_index]=-result_part[7][result_day_index]
            #print result_part[7]
            if result_part[0]*trade_sign >= days_limit:# and result_part[5]*trade_sign >= profit_limit:
                if self.time_range.index(result_part[2]) - self.time_range.index(result_part[1]) > 5 and self.time_range.index(result_part[3]) - self.time_range.index(result_part[2]) > 2 and self.time_range.index(result_part[4]) - self.time_range.index(result_part[3]) > 2:
                    results_timeline_days.append([trade_sign*numpy.median(numpy.array(result_part[7]))/numpy.std(numpy.array(result_part[7]))]+result_part)
            #results_timeline_days.append([result_part[0]]+result_part)
        results_timeline_days.sort()
        if len(results_timeline_days) < 1:
            log.info("No best range for get_best_ranges_profit_std_median")
            return None 
        log.info(results_timeline_days[-20:])
        self.get_list_weight_stat(results_timeline_days[-20:])
        begin_times=[]
        check_times=[]
        start_times=[]
        end_times=[]
        trade_direct=[]
        
        selected_timelines=results_timeline_days[-abs(max_stat):]
        for single_result in selected_timelines:
            begin_times.append(single_result[2])
            check_times.append(single_result[3])
            start_times.append(single_result[4])
            end_times.append(single_result[5])
            trade_direct.append(single_result[6]/abs(single_result[6]))

        begin_dict=Counter(begin_times).most_common()
        check_dict=Counter(check_times).most_common()
        start_dict=Counter(start_times).most_common()
        end_dict=Counter(end_times).most_common()
        trade_dict=Counter(trade_direct).most_common()
        #print begin_dict
                        
        return [[begin_dict[0][0],check_dict[0][0],start_dict[0][0],end_dict[0][0],trade_dict[0][0]]]
    
    def get_day_profit(self, curr_date, period = 30):
        profit_delta=0.25
        procent_delta=1.25
        trade_dir=0
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
        sum_procent_dir=1
        sum_procent_rev=1
        thread_period_dict={"0":2,"1":2,"2":2,"3":2,"5":3,"10":4,"15":5,"30":6,"180":12}
        if "%s" % period in thread_period_dict.keys():
            thread_count = thread_period_dict["%s" % period]
        else:
            thread_count = 16
        curr_date_pos=self.days.index(curr_date)
        log.info("Get day profit %s" % curr_date)
        if curr_date_pos <= period:
            return [-1], [-1], [-1]
        results_days_all,results_profit_all,results_procent_all = self.start_analyzer_threaded(self.days[curr_date_pos-period-1],self.days[curr_date_pos-1],thread_count)
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
        for result in results_procent_all:
            if result[10] == 1:
                results_procent_dir.append(result)
                sum_procent_dir+=(result[0]-1)
            else:
                results_procent_rev.append(result)
                sum_procent_rev+=(result[0]-1)
        #log.info("len dir %s, len rev %s" %(len(results_profit),len(results_procent_rev)))
        """if abs(results_procent[-1][0]) > abs(1/results_procent[0][0])*procent_delta and abs(results_profit[-1][0]-1) > abs(results_profit[0][0]-1) + profit_delta:
            log.info("Good period %s" % (abs(results_procent[-1][0])/abs(1/results_procent[0][0])))
            trade_dir=1
        if abs(results_procent_rev[-1][0]) > abs(1/results_procent_rev[0][0])*procent_delta and abs(results_profit_rev[-1][0]-1) > abs(results_profit_rev[0][0]-1) + profit_delta:
            log.info("Not good period %s" % (abs(results_procent_rev[-1][0])/abs(1/results_procent_rev[0][0])))
            trade_dir=-1
            results_days=results_days_rev
            results_profit=results_profit_rev
            results_procent=results_procent_rev
        #el
        #if abs(results_procent_rev[-1][0]) > abs(1/results_procent_rev[0][0])*procent_delta and abs(results_profit_rev[-1][0]-1) > abs(results_profit_rev[0][0]-1) + profit_delta:
        #    log.info("Not good period %s" % (abs(results_procent_rev[-1][0])/abs(1/results_procent_rev[0][0])))"""
        log.info("Sum_dir %s, sum rev %s" % (sum_procent_dir,sum_procent_rev))
        
        
        if sum_procent_dir < 0 and sum_procent_rev < 0:
            log.info("Good period %s" % (abs(results_procent_dir[-1][0])/abs(1/results_procent_dir[0][0])))
            trade_dir=1
            results_days=results_days_dir
            results_profit=results_profit_dir
            results_procent=results_procent_dir
        elif sum_procent_rev < 0 and sum_procent_dir < 0:
            log.info("Not good period %s" % (abs(results_procent_rev[-1][0])/abs(1/results_procent_rev[0][0])))
            trade_dir=-1
            results_days=results_days_rev
            results_profit=results_profit_rev
            results_procent=results_procent_rev
        if not trade_dir == 0:
            best_ranges1 = self.get_best_ranges_profit_median(results_days, results_profit,8,0.6,period,-5)
            best_ranges2 = self.get_best_ranges_profit_percentile(results_days, results_profit,8,0.6,period,-10)
            best_ranges3 = self.get_best_ranges_profit_std(results_days, results_profit,8,0.6,period,-5)
            best_ranges4 = self.get_best_ranges_profit_std(results_days, results_profit,8,0.6,period,-20)
            best_ranges5 = self.get_best_ranges_profit_std_median(results_days, results_profit,8,0.6,period,-10)
            best_ranges6 = self.get_best_ranges_profit_std_percentile(results_days, results_profit,8,0.6,period,-10)
            best_ranges7 = self.get_best_ranges(results_days, results_profit,8,0.6,period,-5)
            if not best_ranges1 or not best_ranges2 or not best_ranges3 or not best_ranges4 or not best_ranges5 or not best_ranges6 or not best_ranges7:
                log.info("No some best ranges, lets skip")
                return [-1], [-1], [-1]
            best_ranges = best_ranges1 + best_ranges2 + best_ranges3 + best_ranges4 + best_ranges5 + best_ranges6 + best_ranges7
            
            for best_range in best_ranges:
                #begin_time,check_time,start_time,end_time = 100000, 111000, 143000, 180000
                begin_time,check_time,start_time,end_time = best_range[0], best_range[1], best_range[2], best_range[3]
                log.info("Begin %s, check %s, start %s, end %s,trade direct %s" % (begin_time,check_time,start_time,end_time,best_range[4]))
                day_tickers = self.filter_tickers(self.tickers, begin_time,end_time,curr_date,curr_date)
                day_profit, day_count, day_procent, day_list_profit = self.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, 0.0015, 0.015, trade_dir, 200)
                day_profit_list.append(day_profit)
                day_count_list.append(day_count)
                log.info("day_profit %s, day_count %s, day_procent %s" % (day_profit, day_count, day_procent))
                trade_direction_list.append(trade_dir)
        else:
            for i in range(7):
                day_profit_list.append(0)
                day_count_list.append(1)
                log.info("day_profit %s, day_count %s, day_procent %s" % (0, 1, 1))
                trade_direction_list.append(1)
        
        if sum_procent_dir > 5000 and sum_procent_rev < sum_procent_dir:
            log.info("Good period %s" % (abs(results_procent_dir[-1][0])/abs(1/results_procent_dir[0][0])))
            trade_dir=1
            results_days=results_days_dir
            results_profit=results_profit_dir
            results_procent=results_procent_dir
        elif sum_procent_rev > 5000 and sum_procent_dir < sum_procent_rev:
            log.info("Not good period %s" % (abs(results_procent_rev[-1][0])/abs(1/results_procent_rev[0][0])))
            trade_dir=-1
            results_days=results_days_rev
            results_profit=results_profit_rev
            results_procent=results_procent_rev
        if not trade_dir == 0:
            best_ranges1 = self.get_best_ranges_profit_median(results_days, results_profit,8,0.6,period,-5)
            best_ranges2 = self.get_best_ranges_profit_percentile(results_days, results_profit,8,0.6,period,-10)
            best_ranges3 = self.get_best_ranges_profit_std(results_days, results_profit,8,0.6,period,-5)
            best_ranges4 = self.get_best_ranges_profit_std(results_days, results_profit,8,0.6,period,-20)
            best_ranges5 = self.get_best_ranges_profit_std_median(results_days, results_profit,8,0.6,period,-10)
            best_ranges6 = self.get_best_ranges_profit_std_percentile(results_days, results_profit,8,0.6,period,-10)
            best_ranges7 = self.get_best_ranges(results_days, results_profit,8,0.6,period,-5)
            if not best_ranges1 or not best_ranges2 or not best_ranges3 or not best_ranges4 or not best_ranges5 or not best_ranges6 or not best_ranges7:
                log.info("No some best ranges, lets skip")
                return [-1], [-1], [-1]
            best_ranges = best_ranges1 + best_ranges2 + best_ranges3 + best_ranges4 + best_ranges5 + best_ranges6 + best_ranges7
            
            for best_range in best_ranges:
                #begin_time,check_time,start_time,end_time = 100000, 111000, 143000, 180000
                begin_time,check_time,start_time,end_time = best_range[0], best_range[1], best_range[2], best_range[3]
                log.info("Begin %s, check %s, start %s, end %s,trade direct %s" % (begin_time,check_time,start_time,end_time,best_range[4]))
                day_tickers = self.filter_tickers(self.tickers, begin_time,end_time,curr_date,curr_date)
                day_profit, day_count, day_procent, day_list_profit = self.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, 0.0015, 0.015, trade_dir, 200)
                day_profit_list.append(day_profit)
                day_count_list.append(day_count)
                log.info("day_profit %s, day_count %s, day_procent %s" % (day_profit, day_count, day_procent))
                #trade_direction_list.append(best_range[4])
                trade_direction_list.append(trade_dir)
        else:
            for i in range(7):
                day_profit_list.append(0)
                day_count_list.append(1)
                log.info("day_profit %s, day_count %s, day_procent %s" % (0, 1, 1))
                trade_direction_list.append(1)

        if sum_procent_dir > sum_procent_rev and abs(sum_procent_dir-sum_procent_rev) < 5000:
            log.info("Good period %s" % (abs(results_procent_dir[-1][0])/abs(1/results_procent_dir[0][0])))
            trade_dir=1
            results_days=results_days_dir
            results_profit=results_profit_dir
            results_procent=results_procent_dir
        elif sum_procent_dir < sum_procent_rev and abs(sum_procent_rev-sum_procent_dir) < 5000:
            log.info("Not good period %s" % (abs(results_procent_rev[-1][0])/abs(1/results_procent_rev[0][0])))
            trade_dir=-1
            results_days=results_days_rev
            results_profit=results_profit_rev
            results_procent=results_procent_rev
        if not trade_dir == 0:
            best_ranges1 = self.get_best_ranges_profit_median(results_days, results_profit,8,0.6,period,-5)
            best_ranges2 = self.get_best_ranges_profit_percentile(results_days, results_profit,8,0.6,period,-10)
            best_ranges3 = self.get_best_ranges_profit_std(results_days, results_profit,8,0.6,period,-5)
            best_ranges4 = self.get_best_ranges_profit_std(results_days, results_profit,8,0.6,period,-20)
            best_ranges5 = self.get_best_ranges_profit_std_median(results_days, results_profit,8,0.6,period,-10)
            best_ranges6 = self.get_best_ranges_profit_std_percentile(results_days, results_profit,8,0.6,period,-10)
            best_ranges7 = self.get_best_ranges(results_days, results_profit,8,0.6,period,-5)
            if not best_ranges1 or not best_ranges2 or not best_ranges3 or not best_ranges4 or not best_ranges5 or not best_ranges6 or not best_ranges7:
                log.info("No some best ranges, lets skip")
                return [-1], [-1], [-1]
            best_ranges = best_ranges1 + best_ranges2 + best_ranges3 + best_ranges4 + best_ranges5 + best_ranges6 + best_ranges7
            
            for best_range in best_ranges:
                #begin_time,check_time,start_time,end_time = 100000, 111000, 143000, 180000
                begin_time,check_time,start_time,end_time = best_range[0], best_range[1], best_range[2], best_range[3]
                log.info("Begin %s, check %s, start %s, end %s,trade direct %s" % (begin_time,check_time,start_time,end_time,best_range[4]))
                day_tickers = self.filter_tickers(self.tickers, begin_time,end_time,curr_date,curr_date)
                day_profit, day_count, day_procent, day_list_profit = self.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, 0.0015, 0.015, trade_dir, 200)
                day_profit_list.append(day_profit)
                day_count_list.append(day_count)
                log.info("day_profit %s, day_count %s, day_procent %s" % (day_profit, day_count, day_procent))
                #trade_direction_list.append(best_range[4])
                trade_direction_list.append(trade_dir)
        else:
            for i in range(7):
                day_profit_list.append(0)
                day_count_list.append(1)
                log.info("day_profit %s, day_count %s, day_procent %s" % (0, 1, 1))
                trade_direction_list.append(1)
        
            
        if sum_procent_dir > 5000 and sum_procent_rev < 0:
            log.info("Good period %s" % (abs(results_procent_dir[-1][0])/abs(1/results_procent_dir[0][0])))
            trade_dir=1
            results_days=results_days_dir
            results_profit=results_profit_dir
            results_procent=results_procent_dir
        elif sum_procent_rev > 5000 and sum_procent_dir < 0:
            log.info("Not good period %s" % (abs(results_procent_rev[-1][0])/abs(1/results_procent_rev[0][0])))
            trade_dir=-1
            results_days=results_days_rev
            results_profit=results_profit_rev
            results_procent=results_procent_rev
        if not trade_dir == 0:
            best_ranges1 = self.get_best_ranges_profit_median(results_days, results_profit,8,0.6,period,-5)
            best_ranges2 = self.get_best_ranges_profit_percentile(results_days, results_profit,8,0.6,period,-10)
            best_ranges3 = self.get_best_ranges_profit_std(results_days, results_profit,8,0.6,period,-5)
            best_ranges4 = self.get_best_ranges_profit_std(results_days, results_profit,8,0.6,period,-20)
            best_ranges5 = self.get_best_ranges_profit_std_median(results_days, results_profit,8,0.6,period,-10)
            best_ranges6 = self.get_best_ranges_profit_std_percentile(results_days, results_profit,8,0.6,period,-10)
            best_ranges7 = self.get_best_ranges(results_days, results_profit,8,0.6,period,-5)
            if not best_ranges1 or not best_ranges2 or not best_ranges3 or not best_ranges4 or not best_ranges5 or not best_ranges6 or not best_ranges7:
                log.info("No some best ranges, lets skip")
                return [-1], [-1], [-1]
            best_ranges = best_ranges1 + best_ranges2 + best_ranges3 + best_ranges4 + best_ranges5 + best_ranges6 + best_ranges7
            
            for best_range in best_ranges:
                #begin_time,check_time,start_time,end_time = 100000, 111000, 143000, 180000
                begin_time,check_time,start_time,end_time = best_range[0], best_range[1], best_range[2], best_range[3]
                log.info("Begin %s, check %s, start %s, end %s,trade direct %s" % (begin_time,check_time,start_time,end_time,best_range[4]))
                day_tickers = self.filter_tickers(self.tickers, begin_time,end_time,curr_date,curr_date)
                day_profit, day_count, day_procent, day_list_profit = self.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, 0.0015, 0.015, trade_dir, 200)
                day_profit_list.append(day_profit)
                day_count_list.append(day_count)
                log.info("day_profit %s, day_count %s, day_procent %s" % (day_profit, day_count, day_procent))
                #trade_direction_list.append(best_range[4])
                trade_direction_list.append(trade_dir)
        else:
            for i in range(7):
                day_profit_list.append(0)
                day_count_list.append(1)
                log.info("day_profit %s, day_count %s, day_procent %s" % (0, 1, 1))
                trade_direction_list.append(1)

        return day_profit_list, day_count_list,trade_direction_list
        
    def robot(self, date_start=-1, period = 10):
        self.tickers = self.filter_tickers(self.tickers, 100000,184000)
        if date_start > 0:
            self.days.sort()
            date_start_index=self.days.index(date_start)
            self.days=self.days[-len(self.days)+date_start_index-period-1:]
        total_profit = []
        total_count = []
        total_procent_profit = []
        for single_day in self.days:
            day_analyze_time_start=time.time()
            day_profit_list, day_count_list,trade_direction_list= self.get_day_profit(single_day, period)
            if len(total_profit) <= len(day_profit_list):
                for check_func in range(len(day_profit_list)):
                    day_count=day_count_list[check_func]
                    day_profit=day_profit_list[check_func]
                    trade_direction=trade_direction_list[check_func]
                    if len(total_profit)<check_func+1:
                        total_profit.append(1)
                        total_count.append(0)
                        total_procent_profit.append(1)
                    if day_count > 0:
                        #if trade_direction > 0:
                            log.info("Date %s, profit %s, count %s" % (single_day, day_profit, day_count))
                            total_profit[check_func]=total_profit[check_func]+(day_count-1)
                            total_procent_profit[check_func] = total_procent_profit[check_func]*day_count
                            total_count[check_func]+=day_profit
                        #elif trade_direction < 0:
                        #    log.info("Date %s, profit %s, count %s" % (single_day, -day_profit, day_count))
                            #total_profit=total_profit+(day_count-1)
                            #total_procent_profit = total_procent_profit*day_count
                        #    total_profit[check_func]=total_profit[check_func]+(1/day_count-1)
                        #    total_procent_profit[check_func] = total_procent_profit[check_func]*(1/day_count)
                        #    total_count[check_func]-=day_profit
                    log.info("Method %s!!! Total profit %s, total procent profit %s, total count %s, time %s" % (check_func,total_profit[check_func],total_procent_profit[check_func],total_count[check_func], time.time()-day_analyze_time_start))
        return total_profit, total_count

if __name__ == "__main__":
    pa = ProfileAnalyser("TATN_150101_170506.txt")
    start_timer=time.time()
    
    #print pa.analyze_by_day(day_tickers, 104000, 115000, 180000, 0, 0.0015)
    #print pa.analyze_by_day(day_tickers, 125000, 141000, 165000, 0, 0.0015)
    #print pa.analyze_by_day(pa.tickers, 111000, 143000, 175000, 0, 0.0015)
    #print pa.analyze_by_day(pa.tickers, 111000, 144000, 175000, 0, 0.0015)
    #print pa.analyze_by_day(pa.tickers, 111000, 142000, 175000, 0, 0.0015)
    log.info(pa.robot(20150105,5))
    #print pa.start_analyzer_threaded()
    #day_tickers = pa.filter_tickers(pa.tickers, 100000,184000)
    #log.info( pa.analyze_by_day(day_tickers, 111000, 143000, 180000, 0, 0.0015))
    """dates=[20150105,20150401,20150701,20151001,20160101,20160401,20160701,20161001,20170101,20170505]
    #for sdi in range(len(dates)-2):
    day_tickers = pa.filter_tickers(pa.tickers, 100000,184000,-1,-1)
    results_days, results_profit = pa.start_analyzer_threaded(day_start=-1,day_end=-1,threads=16)
    begin_time,check_time,start_time,end_time,trade = pa.get_best_ranges_profit_std(results_days, results_profit,8,0.6,-10)[0]
    log.info("Time 1")
    log.info( "%s. %s. %s, %s" % (begin_time,check_time,start_time,end_time))
    log.info( "Result 1")
    log.info( pa.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, 0.0015))
    begin_time,check_time,start_time,end_time,trade = pa.get_best_ranges_profit_percentile(results_days, results_profit,8,0.6,-5)[0]
    log.info( "Time 2")
    log.info( "%s. %s. %s, %s" % (begin_time,check_time,start_time,end_time))
    log.info( "Result 2")
    log.info( pa.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, 0.0015))
    log.info( "Result 3")
    log.info( pa.analyze_by_day(day_tickers, 124000, 132000, 152000, 0, 0.0015))
    #results_days, results_profit = pa.start_analyzer_threaded(day_start=20160225,day_end=20160225,threads=1)
    print "2, 0.6"
    begin_time,check_time,start_time,end_time = pa.get_best_ranges(results_days, results_profit,2,0.6)
    print begin_time,check_time,start_time,end_time
    print "%s %s" % pa.analyze_by_day(pa.tickers, check_time, start_time, end_time, 0, 0.001)
    print "8, 0.6"
    begin_time,check_time,start_time,end_time = pa.get_best_ranges(results_days, results_profit,8,0.8)
    print begin_time,check_time,start_time,end_time
    print "%s %s" % pa.analyze_by_day(pa.tickers, check_time, start_time, end_time, 0, 0.001)
    print "%s %s" % pa.analyze_by_day(pa.tickers, 111000, 143000, 180000, 0, 0.001)
    print "16, 0.6"
    begin_time,check_time,start_time,end_time = pa.get_best_ranges(results_days, results_profit,16,0.6)
    print begin_time,check_time,start_time,end_time
    print "%s %s" % pa.analyze_by_day(pa.tickers, check_time, start_time, end_time, 0, 0.002)
    print "24, 0.6"
    begin_time,check_time,start_time,end_time = pa.get_best_ranges(results_days, results_profit,24,0.6)
    print begin_time,check_time,start_time,end_time
    print "%s %s" % pa.analyze_by_day(pa.tickers, check_time, start_time, end_time, 0, 0.002)
    print "32, 0.6"
    begin_time,check_time,start_time,end_time = pa.get_best_ranges(results_days, results_profit,32,0.6)
    print begin_time,check_time,start_time,end_time
    print "%s %s" % pa.analyze_by_day(pa.tickers, check_time, start_time, end_time, 0, 0.002)
    print "40, 0.8"
    begin_time,check_time,start_time,end_time = pa.get_best_ranges(results_days, results_profit,40,0.6)
    print begin_time,check_time,start_time,end_time
    print "%s %s" % pa.analyze_by_day(pa.tickers, check_time, start_time, end_time, 0, 0.002)
    print "64, 0.6"
    begin_time,check_time,start_time,end_time = pa.get_best_ranges(results_days, results_profit,64,0.6)
    print begin_time,check_time,start_time,end_time
    print "%s %s" % pa.analyze_by_day(pa.tickers, check_time, start_time, end_time, 0, 0.002)
    print "80, 0.6"
    begin_time,check_time,start_time,end_time = pa.get_best_ranges(results_days, results_profit,80,0.6)
    print begin_time,check_time,start_time,end_time
    print "%s %s" % pa.analyze_by_day(pa.tickers, check_time, start_time, end_time, 0, 0.002)
    print "128, 0.6"
    begin_time,check_time,start_time,end_time = pa.get_best_ranges(results_days, results_profit,128,0.6)
    print begin_time,check_time,start_time,end_time
    print "%s %s" % pa.analyze_by_day(pa.tickers, check_time, start_time, end_time, 0, 0.002)
    #for delta in [0,1,1.5,2,2.5,3,3.5]:
    #filtered_tickers = pa.filter_tickers(pa.tickers, 100000, 175000)
    print "%s %s" % pa.analyze_by_day(pa.tickers, 111000, 143000, 180000, 0, 0.5)
    print "%s %s" % pa.analyze_by_day(filtered_tickers, 111000, 143000, 180000, 0, 0.5)
    print "%s %s" % pa.analyze_by_day(filtered_tickers, 111000, 143000, 175000, 0, 0)
    print "%s %s" % pa.analyze_by_day(filtered_tickers, 111000, 143000, 175000, 0, 0.5)
    print "%s %s" % pa.analyze_by_day(filtered_tickers, 111000, 143000, 174000, 0, 0)
    print "%s %s" % pa.analyze_by_day(filtered_tickers, 111000, 143000, 174000, 0, 0.5)
    print "%s %s" % pa.analyze_by_day(filtered_tickers, 111000, 143000, 173000, 0, 0)
    print "%s %s" % pa.analyze_by_day(filtered_tickers, 111000, 143000, 173000, 0, 0.5)
    print "%s %s" % pa.analyze_by_day(filtered_tickers, 115000, 143000, 180000, 0, 0)
    print "%s %s" % pa.analyze_by_day(filtered_tickers, 115000, 143000, 180000, 0, 0.5)
    print "%s %s" % pa.analyze_by_day(filtered_tickers, 115000, 143000, 171000, 0, 0)
    print "%s %s" % pa.analyze_by_day(filtered_tickers, 115000, 143000, 171000, 0, 0.5)
    print "%s %s" % pa.analyze_by_day(filtered_tickers, 115000, 143000, 164000, 0, 0)
    print "%s %s" % pa.analyze_by_day(filtered_tickers, 115000, 143000, 164000, 0, 0.5)
    print "%s %s" % pa.analyze_by_day(filtered_tickers, 115000, 143000, 161000, 0, 0)
    print "%s %s" % pa.analyze_by_day(filtered_tickers, 115000, 143000, 161000, 0, 0.5)
    day_tickers = pa.filter_tickers(pa.tickers, 100000,184000,20150311,20150311)
    log.info( pa.analyze_by_day(day_tickers, 110000, 152000, 175000, 0, 0.0015,0.015,1,0.015))
    day_tickers = pa.filter_tickers(pa.tickers, 100000,184000,20150401,20150701)
    log.info( pa.analyze_by_day(day_tickers, 124000, 132000, 152000, 0, 0.0015))
    day_tickers = pa.filter_tickers(pa.tickers, 100000,184000,20150705,20151001)
    log.info( pa.analyze_by_day(day_tickers, 124000, 132000, 152000, 0, 0.0015))
    day_tickers = pa.filter_tickers(pa.tickers, 100000,184000,20151001,20160101)
    log.info( pa.analyze_by_day(day_tickers, 124000, 132000, 152000, 0, 0.0015))
    day_tickers = pa.filter_tickers(pa.tickers, 100000,184000,20160101,20160401)
    log.info( pa.analyze_by_day(day_tickers, 124000, 132000, 152000, 0, 0.0015))
    day_tickers = pa.filter_tickers(pa.tickers, 100000,184000,20160401,20160701)
    log.info( pa.analyze_by_day(day_tickers, 124000, 132000, 152000, 0, 0.0015))
    day_tickers = pa.filter_tickers(pa.tickers, 100000,184000,20160705,20161001)
    log.info( pa.analyze_by_day(day_tickers, 124000, 132000, 152000, 0, 0.0015))
    day_tickers = pa.filter_tickers(pa.tickers, 100000,184000,20161001,20170101)
    log.info( pa.analyze_by_day(day_tickers, 124000, 132000, 152000, 0, 0.0015))
    day_tickers = pa.filter_tickers(pa.tickers, 100000,184000,20170101,-1)
    log.info( pa.analyze_by_day(day_tickers, 124000, 132000, 152000, 0, 0.0015))"""

    log.info( time.time()-start_timer)