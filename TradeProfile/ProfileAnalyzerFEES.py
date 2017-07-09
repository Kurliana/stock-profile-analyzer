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
logging.config.fileConfig('log_fees.conf')
log=logging.getLogger('main')
from ProfileAnalyzer import ProfileAnalyser

class ProfileAnalyserFEES(ProfileAnalyser):
    
    def get_ranges_by_dayweek(self,curr_date):
        day_of_week = datetime.datetime(int(str(curr_date)[:4]), int(str(curr_date)[4:6]), int(str(curr_date)[6:8]), 23, 55, 55, 173504).weekday()
        day_ranges={0:[100000, 112000, 155000, 180000,1],
                    1:[100000, 171000, 172000, 175000,1],
                    2:[100000, 112000, 141000, 172000,-1],
                    3:[100000, 113000, 163000, 170000,1],
                    4:[100000, 132000, 135000, 162000,1],
                    5:[183000, 183000, 183000, 183000,1],
                    6:[183000, 183000, 183000, 183000,1]}

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

        #if self.get_ranges_by_dayweek_new(curr_date)[0][4] == 1:
        results_days=results_days_dir
        #else:
        #    results_days=results_days_rev
        #    results_profit=results_profit_rev
        #    results_procent=results_procent_rev
        #else:
            #return  [-1], [-1], [-1], []
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
        best_ranges10 = self.get_ranges_by_dayweek_new(curr_date)
        if not best_ranges1 or not best_ranges2 or not best_ranges3 or not best_ranges4 or not best_ranges5 or not best_ranges6 or not best_ranges7 or not best_ranges8:
            log.info("No some best ranges, lets skip")
            return [-1], [-1], [-1], []
        best_ranges = best_ranges1 + best_ranges2 + best_ranges3 + best_ranges4 + best_ranges5 + best_ranges6 + best_ranges7 + best_ranges8+best_ranges9+best_ranges10

        for best_range in best_ranges:
            used_ranges.append(best_range + [0.0015, loss, 200])
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
            used_ranges.append(best_range + [0.01, loss, 200])
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
            used_ranges.append(best_range + [0.0015, 0.02, 200])
            ranges_counter+=1
            begin_time,check_time,start_time,end_time = best_range[0], best_range[1], best_range[2], best_range[3]
            day_profit, day_count, day_procent, day_list_profit = self.analyze_by_day(period_day_tickers, check_time, start_time, end_time, 0, 0.0015, 0.02, best_range[4], 200, True)
            log.info("Period %s: day_profit %s, day_count %s, day_procent %s" % (ranges_counter,day_profit, day_count, day_procent))
            log.info("Begin %s, check %s, start %s, end %s,trade direct %s" % (begin_time,check_time,start_time,end_time,best_range[4]))
            if simulate_trade:
                day_tickers = self.filter_tickers(self.tickers, begin_time,end_time,curr_date,curr_date)
                day_profit, day_count, day_procent, day_list_profit = self.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, 0.0015, 0.02, best_range[4], 200, True)
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
            used_ranges.append(best_range + [0.0015, 0.01, 200])
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

        
        return day_profit_list, day_count_list,trade_direction_list,used_ranges
           
    def robot(self, date_start=-1, period = 10, period2 = 0, day_end = -1):
        self.tickers = self.filter_tickers(self.tickers, 100000,184000,-1,-1)
        if date_start > 0:
            date_start_index=self.days.index(date_start)
            self.days=self.days[-len(self.days)+date_start_index-max(period,period2*5)-1:]
        if day_end > 0 and day_end not in self.days:
            self.days.append(day_end)
        total_profit_list=[]
        total_profit = []
        total_count = []
        total_procent_profit = []
        total_extra_profit = []
        changer_period=120
        for single_day in self.days:
            if day_end < 0 or day_end > single_day:
                day_analyze_time_start=time.time()
                day_profit_list, day_count_list,trade_direction_list,used_ranges=self.get_day_profit_old(single_day, period,period2)
                if len(total_profit_list) > changer_period:           
                    accumul_prof=1
                    best_prof=1.9
                    if len(day_count_list) > 18: 
                        for saved_prof_ind in range(min(len(day_count_list),40)):
                            method_per_prof=1
                            for prev_profit in range(changer_period):
                                method_per_prof=method_per_prof*total_profit_list[-prev_profit-1][saved_prof_ind]
                            log.info("TotalProfit method %s: %s with day profit %s" % (saved_prof_ind,method_per_prof,day_count_list[saved_prof_ind]))
                            if method_per_prof > best_prof:
                                #if method_per_prof > 1.9 and saved_prof_ind in [0,2]:
                                #    accumul_prof = 1
                                #    break
                                if saved_prof_ind in [8, 9, 15, 39] and method_per_prof < 7: #[0,8,10,14]
                                    log.info("Let's use method %s with times %s" % (saved_prof_ind,used_ranges[saved_prof_ind]))
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
        if day_end > 0:            
            saved_times=None
            day_analyze_time_start=time.time()
            day_profit_list, day_count_list,trade_direction_list,used_ranges=self.get_day_profit_old(day_end, period,period2,simulate_trade=False)
            if len(total_profit_list) > changer_period:           
                accumul_prof=1
                best_prof=1.9
                if len(day_count_list) > 18: 
                    for saved_prof_ind in range(min(len(day_count_list),40)):
                        method_per_prof=1
                        for prev_profit in range(changer_period):
                            method_per_prof=method_per_prof*total_profit_list[-prev_profit-1][saved_prof_ind]
                        log.info("TotalProfit method %s: %s with day profit %s" % (saved_prof_ind,method_per_prof,day_count_list[saved_prof_ind]))
                        if method_per_prof > best_prof:
                            #if method_per_prof > 1.9 and saved_prof_ind in [0,2]:
                            #    accumul_prof = 1
                            #    break
                            if saved_prof_ind in [8, 9, 15, 39] and method_per_prof < 7: #[0,8,10,14]
                                log.info("Let's finally use method %s with times %s" % (saved_prof_ind,used_ranges[saved_prof_ind]))
                                best_prof = method_per_prof
                                accumul_prof = day_count_list[saved_prof_ind]
                                saved_times=used_ranges[saved_prof_ind]
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
                            log.info("Date %s, profit %s, count %s" % (day_end, day_profit, day_count))
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
        return [saved_times]

if __name__ == "__main__":
    # based on my_app_super_full_fees_30_new_fast_p3x120_fixed_times
    start_timer=time.time()
    temp_file_name="daily_FEES.txt"
    result_file="C:\Just2Trade Client\FEES.txt"
    if os.path.exists(temp_file_name):
        os.remove(temp_file_name)
    cur_date=time.localtime()
    cur_year=cur_date[0]
    cur_month=cur_date[1]
    cur_day=cur_date[2]
    results_days=[]
    results_profit=[]
    results_procent=[]
    results_days_rev=[]
    results_profit_rev=[]
    results_procent_rev=[]
    results_days_dir=[]
    results_profit_dir=[]
    results_procent_dir=[]
    get_file_string="http://export.finam.ru/export9.out"
    
    stock_params={"market":"1",
                  "em":"20509",
                  "code":"FEES",
                  "apply":"0",
                  "df":"1",
                  "mf":"7",
                  "yf":"2016",
                  "from":"01.08.2016",
                  "dt":"%s" % cur_day,
                  "mt":"%s" % (cur_month-1),
                  "yt":"%s" % cur_year,
                  "to":"%s.%s.%s" % (cur_day,cur_month,cur_year),
                  "p":"4", # period means 10 minutes
                  "e":".txt", # export format
                  "f":"%s" % temp_file_name.split(".")[0],
                  "cn":"FEES",
                  "dtf":"1",
                  "tmf":"1",
                  "sep":"1",
                  "sep2":"1",
                  "datf":"1",
                  "at":"0",
                  "fsp":"1",
                  "MSOR":"1",                 
                  }
    r = requests.post(get_file_string, stock_params,stream=True,allow_redirects=True)
    with open(temp_file_name, 'wb') as f:
        shutil.copyfileobj(r.raw, f)
        
    pa = ProfileAnalyserFEES(temp_file_name)
    log.info("All saved dayes %s " % len(pa.days))
    start_date=pa.days[-133]
    best_range = pa.robot(start_date, 30, day_end = int("%d%.2d%.2d" % (cur_year,cur_month,cur_day)))[0]
    
    if not best_range:
        with open(result_file, 'wb') as f:
            f.write("\n")
            #f.write("00\n")
            #f.write("00\n")
            #f.write("00\n")
            #f.write("00\n")
            #f.write("00\n")
    else:    
        begin_time,check_time,start_time,end_time,trade,delta,loss,take = best_range[0], best_range[1], best_range[2], best_range[3], best_range[4], best_range[5], best_range[6], best_range[7]               
        #current_date=datetime.date.today().strftime("%Y%m%d")
        #begin_time,check_time,start_time,end_time,trade = pa.get_ranges_by_dayweek(int(current_date))[0]
        #log.info("Current date %s" % current_date)
        #period_day_tickers = pa.filter_tickers(pa.tickers, 100000,184000,pa.days[-6],pa.days[-1])
        #day_profit, day_count, day_procent, day_list_profit = pa.analyze_by_day(period_day_tickers, check_time, start_time, end_time, 0, 0.0005, 0.015, 1, 0.02, True)
        with open(result_file, 'wb') as f:
            f.write(str(check_time)[:2]+"\n")
            f.write(str(check_time)[2:4]+"\n")
            f.write(str(start_time)[:2]+"\n")
            f.write(str(start_time)[2:4]+"\n")
            f.write(str(end_time)[:2]+"\n")
            f.write(str(end_time)[2:4]+"\n")
            f.write(str(trade)+"\n")
            f.write(str(delta)+"\n")
            f.write(str(loss)+"\n")
            f.write(str(take)+"\n")

    log.info( time.time()-start_timer)