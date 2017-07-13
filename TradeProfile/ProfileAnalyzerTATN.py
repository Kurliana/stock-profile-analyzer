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

logging.config.fileConfig('log_tatn.conf')
log=logging.getLogger('main')
from ProfileAnalyzer import ProfileAnalyser

class ProfileAnalyserTATN(ProfileAnalyser):
    
    def get_day_week(self,curr_date):
        return datetime.datetime(int(str(curr_date)[:4]), int(str(curr_date)[4:6]), int(str(curr_date)[6:8]), 23, 55, 55, 173504).weekday()

    def get_ranges_by_dayweek(self,curr_date):
        day_of_week =  self.get_day_week(curr_date)
        day_ranges={0:[100000, 122000, 132000, 174000,1],
                    1:[100000, 104000, 130000, 165000,1],
                    2:[100000, 110000, 112000, 131000,1],
                    3:[100000, 125000, 130000, 154000,1],
                    4:[100000, 112000, 122000, 173000,1],
                    5:[183000, 183000, 183000, 183000,1],
                    6:[183000, 183000, 183000, 183000,1]}

        return [day_ranges[day_of_week]]

    def get_ranges_by_dayweek_new(self,curr_date):
        day_of_week = self.get_day_week(curr_date)
        day_ranges={0:[100000, 122000, 133000, 174000,1],
                    1:[100000, 104000, 130000, 165000,1],
                    2:[100000, 104000, 112000, 130000,1],
                    3:[100000, 123000, 124000, 154000,1],
                    4:[100000, 113000, 132000, 171000,1],
                    5:[183000, 183000, 183000, 183000,1],
                    6:[183000, 183000, 183000, 183000,1]}
        return [day_ranges[day_of_week]]
    
    def get_day_profit_old(self, curr_date, period = 30,period2 = 30,simulate_trade=True,delta=0.005,loss=0.015):
        used_ranges=[]
        ranges_counter=0
        profit_delta=0.25
        procent_delta=1.25
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
        self.success_ranges.append(success_day_counter)
        if len(self.success_ranges) > 1:
            if success_day_counter - self.success_ranges[-2] > 2000:
                log.info("Too big increase of success ranges %s" % (success_day_counter - self.success_ranges[-2]))
                return [-1], [-1], [-1], []
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
       # else:
        #    results_days=results_days_rev
        #    results_profit=results_profit_rev
        #    results_procent=results_procent_rev
        #else:
            #return  [-1], [-1], [-1], []
        #else:
        #    return  [-1], [-1], [-1]
       
        best_ranges1 = self.get_best_ranges_new_gen("median",results_days, 8,0.6,period,-5)
        best_ranges2 = self.get_best_ranges_new_gen("extra2",results_days, 8,0.6,30,-5)
        best_ranges3 = self.get_best_ranges_new_gen("simple_profit",results_days, 8,0.6,period,-5)
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

        for tmp_delta, tmp_loss, tmp_prof in [[0.005, loss, 200],[0.01, loss, 200],[0.0015, loss, 200],[0.005, 0.02, 200]]:
            for best_range in best_ranges:
                used_ranges.append(best_range+[tmp_delta, tmp_loss, tmp_prof])
                ranges_counter+=1
                begin_time,check_time,start_time,end_time = best_range[0], best_range[1], best_range[2], best_range[3]
                day_profit, day_count, day_procent, day_list_profit = self.analyze_by_day(period_day_tickers, check_time, start_time, end_time, 0, tmp_delta, tmp_loss, best_range[4], tmp_prof, True)
                log.info("Period %s: day_profit %s, day_count %s, day_procent %s" % (ranges_counter,day_profit, day_count, day_procent))
                log.info("Begin %s, check %s, start %s, end %s,trade direct %s" % (begin_time,check_time,start_time,end_time,best_range[4]))
                if simulate_trade:
                    day_tickers = self.filter_tickers(self.tickers, begin_time,end_time,curr_date,curr_date)
                    day_profit, day_count, day_procent, day_list_profit = self.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, tmp_delta, tmp_loss, best_range[4], tmp_prof, True)
                    day_profit_list.append(day_profit)
                    day_count_list.append(day_count)
                    log.info("day_profit %s %s, day_count %s, day_procent %s" % (ranges_counter,day_profit, day_count, day_procent))
                    trade_direction_list.append(best_range[4])
                else:
                    day_profit_list.append(0)
                    day_count_list.append(1)
                    log.info("day_profit %s, day_count %s, day_procent %s" % (0, 1, 1))
                    trade_direction_list.append(1)
            
        return day_profit_list, day_count_list,trade_direction_list,used_ranges
           
    def robot(self, date_start=-1, period = 10, period2 = 0, day_end = -1, delta = 0.0015, loss = 0.015):
        self.tickers = self.filter_tickers(self.tickers, 100000,184000,-1,-1)
        best_prof=0.3
        max_prof=3
        methods_list=[8,9,39]
        if date_start > 0:
            date_start_index=self.days.index(date_start)
            """for i in range(10):
                reserv_tickers=[]
                results_procent_dir=[]
                results_procent_rev=[]
                reserv_tickers+=self.tickers
                curr_date=self.days[date_start_index-i]
                dayweek = self.get_day_week(curr_date)
                if not self.allowed_times[dayweek]:
                    self.tickers=self.filter_tickers(self.tickers, 100000,184000,-1,-1,dayweek)
                    results_days_all,results_profit_all,results_procent_all = self.start_analyzer_threaded(-1,-1,4,delta,loss)
                    for result in results_procent_all:
                        if result[10] == 1:
                            results_procent_dir.append(result)
                        else:
                            results_procent_rev.append(result)
                    if self.get_ranges_by_dayweek(curr_date)[0][4] == 1:
                        results_procent=results_procent_dir
                    else:
                        results_procent=results_procent_rev
                    self.set_allowed_times(results_procent[-50:],dayweek)
                    self.tickers=reserv_tickers
                    del reserv_tickers
                    del results_procent_all
                    del results_procent_dir
                    del results_procent_rev
                    del results_days_all
                    del results_profit_all"""
            self.days=self.days[-len(self.days)+date_start_index-max(period,period2*5)-1:]
        if day_end > 0 and day_end not in self.days:
            self.days.append(day_end)

        #check
        for day in self.days:
            day_got=0
            for ticker in self.tickers:
                if ticker[3] == 101000 and ticker[2]==day:
                    day_got = 1
            if day_got == 0:
                log.info("No start tickers found for day %s" % day)

        total_profit_list=[]
        total_profit = []
        total_count = []
        total_procent_profit = []
        total_extra_profit = []
        saved_times=[]
        changer_period=3
        for single_day in self.days:
            if day_end < 0 or day_end > single_day:
                day_analyze_time_start=time.time()
                day_profit_list, day_count_list,trade_direction_list,used_ranges=self.get_day_profit_old(single_day, period,period2,delta=delta,loss=loss)
                if len(total_profit_list) > changer_period:           
                    accumul_prof=1
                    tmp_best_prof=best_prof
                    if len(day_count_list) > 18: 
                        for saved_prof_ind in range(min(len(day_count_list),40)):
                            method_per_prof=1
                            for prev_profit in range(changer_period):
                                method_per_prof=method_per_prof*total_profit_list[-prev_profit-1][saved_prof_ind]
                            log.info("TotalProfit method %s: %s with day profit %s" % (saved_prof_ind,method_per_prof,day_count_list[saved_prof_ind]))
                            if method_per_prof > tmp_best_prof:
                                #if method_per_prof > 1.9 and saved_prof_ind in [0,2]:
                                #    accumul_prof = 1
                                #    break
                                if saved_prof_ind in methods_list and method_per_prof < max_prof: #[0,8,10,14]
                                    log.info("Let's use method %s with times %s" % (saved_prof_ind,used_ranges[saved_prof_ind]))
                                    tmp_best_prof = method_per_prof
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
                    for check_func in range(min(len(day_profit_list),len(day_count_list))):
                        day_count=day_count_list[check_func]
                        day_profit=day_profit_list[check_func]
                        if len(total_profit)<check_func+1:
                            total_profit.append(1)
                            total_count.append(0)
                            total_procent_profit.append(1)
                            total_extra_profit.append(1)
                        if day_count > 0:
                                log.info("Date %s, profit %s, count %s" % (single_day, day_profit, day_count))
                                total_profit[check_func]=total_profit[check_func]+(day_count-1)
                                total_procent_profit[check_func] = total_procent_profit[check_func]*day_count
                                total_count[check_func]+=day_profit
                                total_extra_profit[check_func]=max(total_extra_profit[check_func]-round(total_extra_profit[check_func]/2)+round(total_extra_profit[check_func]/2)*day_count,1)
                        log.info("Method %s!!! Total profit %s, total procent profit %s, total count %s, total extra profit %s,time %s" % (check_func,total_profit[check_func],total_procent_profit[check_func],total_count[check_func], total_extra_profit[check_func], time.time()-day_analyze_time_start))
                    if len(day_profit_list) > 1:
                        total_profit_list.append(day_count_list)
        if day_end > 0:            
            saved_times=None
            day_analyze_time_start=time.time()
            day_profit_list, day_count_list,trade_direction_list,used_ranges=self.get_day_profit_old(day_end, period,period2,simulate_trade=False,delta=delta,loss=loss)
            if len(total_profit_list) > changer_period:           
                accumul_prof=1
                tmp_best_prof=best_prof
                if len(day_count_list) > 18: 
                    for saved_prof_ind in range(min(len(day_count_list),40)):
                        method_per_prof=1
                        for prev_profit in range(changer_period):
                            method_per_prof=method_per_prof*total_profit_list[-prev_profit-1][saved_prof_ind]
                        log.info("TotalProfit method %s: %s with day profit %s" % (saved_prof_ind,method_per_prof,day_count_list[saved_prof_ind]))
                        if method_per_prof > tmp_best_prof:
                            if saved_prof_ind in methods_list and method_per_prof < max_prof: #[0,8,10,14]
                                log.info("Let's finally use method %s with times %s" % (saved_prof_ind,used_ranges[saved_prof_ind]))
                                tmp_best_prof = method_per_prof
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
                for check_func in range(min(len(day_profit_list),len(day_count_list))):
                    day_count=day_count_list[check_func]
                    day_profit=day_profit_list[check_func]
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
                    log.info("Method %s!!! Total profit %s, total procent profit %s, total count %s, total extra profit %s,time %s" % (check_func,total_profit[check_func],total_procent_profit[check_func],total_count[check_func], total_extra_profit[check_func], time.time()-day_analyze_time_start))
                if len(day_profit_list) > 1:
                    total_profit_list.append(day_count_list)
        return [saved_times]
    
    
if __name__ == "__main__":
    # based on my_app_super_full_tatn_5_p3x3_double_ranges
    start_timer=time.time()
    temp_file_name="daily_TATN.txt"
    result_file="C:\Just2Trade Client\TATN.txt"
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
                  "em":"825",
                  "code":"TATN",
                  "apply":"0",
                  "df":"2",
                  "mf":"4",
                  "yf":"2017",
                  "from":"02.05.2017",
                  "dt":"%s" % cur_day,
                  "mt":"%s" % (cur_month-1),
                  "yt":"%s" % cur_year,
                  "to":"%s.%s.%s" % (cur_day,cur_month,cur_year),
                  "p":"4", # period means 10 minutes
                  "e":".txt", # export format
                  "f":"%s" % temp_file_name.split(".")[0],
                  "cn":"TATN",
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
        
    pa = ProfileAnalyserTATN(temp_file_name)
    log.info("All saved dayes %s " % len(pa.days))
    start_date=pa.days[-10]
    best_range = pa.robot(start_date, 5, day_end = int("%d%.2d%.2d" % (cur_year,cur_month,cur_day)),delta=0.005,loss=0.015)[0]
    
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