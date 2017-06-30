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

if __name__ == "__main__":
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
        
    pa = ProfileAnalyser(temp_file_name)
    log.info("All saved dayes %s " % len(pa.days))
    start_date=pa.days[-123]
    best_range = pa.robot(start_date, 30, day_end = pa.days[-2])[0]
    
    if not best_range:
        with open(result_file, 'wb') as f:
            f.write("\n")
            #f.write("00\n")
            #f.write("00\n")
            #f.write("00\n")
            #f.write("00\n")
            #f.write("00\n")
    else:    
        begin_time,check_time,start_time,end_time = best_range[0], best_range[1], best_range[2], best_range[3]                
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

    log.info( time.time()-start_timer)