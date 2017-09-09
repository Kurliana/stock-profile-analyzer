'''
Created on 25 Aug 2017

@author: Kurliana
'''

import sys
import pyopencl as cl
import numpy as np

class clAnalyzer:
    
    def __init__(self,tickers,begin_list,check_list,start_list,end_list,delta_list,stop_list,take_list,profit_list,comission,go):
        self.plat = cl.get_platforms()
        self.GPU = self.plat[0].get_devices()[0]
        print("Device name:", self.GPU.name)
        self.CPU = self.plat[0].get_devices()[1]
        print("Device name:", self.CPU.name)
        self.ctx = cl.Context([self.GPU])
        self.ctx2 = cl.Context([self.GPU])
         
        # Create queue for each kernel execution
        self.queue = cl.CommandQueue(self.ctx)
        self.queue2 = cl.CommandQueue(self.ctx2)
         
        self.mf = cl.mem_flags
        self.tickers_g =  cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=np.array(tickers,dtype=np.float64))
        self.begin_list_g =  cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=np.array(begin_list,dtype=np.int32))
        self.check_list_g =  cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=np.array(check_list,dtype=np.int32))
        self.start_list_g =  cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=np.array(start_list,dtype=np.int32))
        self.end_list_g =  cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=np.array(end_list,dtype=np.int32))
        self.delta_list_g =  cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=np.array(delta_list,dtype=np.float64))
        self.stop_list_g =  cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=np.array(stop_list,dtype=np.float64))
        self.take_list_g =  cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=np.array(take_list,dtype=np.float64))
        self.profit_list_g =  cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=np.array(profit_list,dtype=np.float64))
        
        self.height_g = cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=np.int32(len(tickers)))
        
        self.comission_g = cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR , hostbuf=np.float64(comission))
        self.go_g = cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=np.int32(go))
        self.main_code= """

        typedef struct{
            double atr;
            double atr1;
            double atr15;
            double atr2;
            double atr3;
            double atr4;
            double atr5;
            double atr10;
        } tindicator;  
          
          
        typedef struct{
            double ticker_name;
            double ticker_interval;
            double ticker_date;
            double ticker_time;
            double start_price;
            double high_price;
            double low_price;
            double close_price;
            double volume;
            double atr;
            double atr1;
            double atr15;
            double atr2;
            double atr3;
            double atr4;
            double atr5;
            double atr10;
            double ema9;
            double ema14;
            double ema20;
            double ema27;
            double vwap;
            double vwma9;
            double vwma14;
            double vwma20;
            double vwma27;

        } tticker;
       
        typedef struct{
            short begin_time;
            short check_time;
            short start_time;
            short end_time;
            short delta;
            short direction_delta;
            short stop_loss;
            short reverse_trade;
            short take_profit;
            short take_profit_schema;
        } ttradeparam;
        
        int is_up_direction(tticker ticker1, int check_time, double direction_delta){
            if (ticker1.ticker_time > (float) check_time)
                return 0;
            if ((fabs(ticker1.start_price - ticker1.close_price) - min(ticker1.start_price,ticker1.close_price)*direction_delta > 0.00000000000000001) && (ticker1.start_price - ticker1.close_price < 0.00000000000000001))
                return 1;
            else if ((fabs(ticker1.start_price - ticker1.close_price) - min(ticker1.start_price,ticker1.close_price)*direction_delta > 0.00000000000000001) && (ticker1.start_price - ticker1.close_price > 0.00000000000000001))
                return -1;
            else
                return 0;
        }
        
        int is_up_direction_vwap(__global tticker *tickers_list, int start_ticker, int end_ticker, int start_time, int check_time, double direction_delta){
            int direction=0;
            tticker ticker1;
            for(int ticker_number = start_ticker; ticker_number <= end_ticker; ticker_number++){
                ticker1=tickers_list[ticker_number];
                if ((ticker1.ticker_time > (float)start_time) && (ticker1.ticker_time < (float)check_time+1)){
                
                    if (ticker1.vwap < ticker1.close_price )
                        direction+=1;
                    else if (ticker1.vwap > ticker1.close_price)
                        direction-=1;
                }
            }
            if (((float)(abs(direction)) > direction_delta) && (direction != 0))
                return direction/abs(direction);
            else
                return 0;
        }
        
        int is_up_direction2(__global tticker *tickers_list, int start_ticker, int end_ticker, int start_time, int check_time, double direction_delta, int ema1, int ema2){
            tticker total_ticker;
            int total_ticker_exists=0;
            tticker ticker1 = tickers_list[start_ticker];
            tticker ticker2;
            double min_value=20000;
            double min_time=0;
            double max_value=0;
            double max_time=0;
            double close_value=0;
            int total_direction=0;
            double ticker_ema1=-1;
            double ticker_ema2=-1;
            double ticker_vwma1=-1;
            double ticker_vwma2=-1;
                        
            for(int ticker_number = start_ticker+1; ticker_number <= end_ticker; ticker_number++){
                ticker2=tickers_list[ticker_number];
                if ((ticker2.ticker_time > (float)start_time) && (ticker2.ticker_time < (float)check_time+1)){
                    if ((ema1==0) && (ema2==0))
                    {
                        if (ticker_vwma2 < 0)
                            ticker_vwma2=ticker2.start_price;
                        ticker_vwma1=ticker2.close_price;
                    }
                    else if ((ema1>0) && (ema2==0))
                    {
                        ticker_ema1=ticker2.close_price;
                        ticker_vwma1=ticker2.close_price;
                        if (ema1==9) ticker_ema2=ticker2.ema9;
                        if (ema1==14) ticker_ema2=ticker2.ema14;
                        if (ema1==20) ticker_ema2=ticker2.ema20;
                        if (ema1==27) ticker_ema2=ticker2.ema27;
                        if (ema1==9) ticker_vwma2=ticker2.vwma9;
                        if (ema1==14) ticker_vwma2=ticker2.vwma14;
                        if (ema1==20) ticker_vwma2=ticker2.vwma20;
                        if (ema1==27) ticker_vwma2=ticker2.vwma27;
                    }
                    else
                    {
                        if (ema1==9) ticker_ema1=ticker2.ema9;
                        if (ema1==14) ticker_ema1=ticker2.ema14;
                        if (ema1==20) ticker_ema1=ticker2.ema20;
                        if (ema1==27) ticker_ema1=ticker2.ema27;
                        if (ema2==9) ticker_ema2=ticker2.ema9;
                        if (ema2==14) ticker_ema2=ticker2.ema14;
                        if (ema2==20) ticker_ema2=ticker2.ema20;
                        if (ema2==27) ticker_ema2=ticker2.ema27;
                        if (ema1==9) ticker_vwma1=ticker2.vwma9;
                        if (ema1==14) ticker_vwma1=ticker2.vwma14;
                        if (ema1==20) ticker_vwma1=ticker2.vwma20;
                        if (ema1==27) ticker_vwma1=ticker2.vwma27;
                        if (ema2==9) ticker_vwma2=ticker2.vwma9;
                        if (ema2==14) ticker_vwma2=ticker2.vwma14;
                        if (ema2==20) ticker_vwma2=ticker2.vwma20;
                        if (ema2==27) ticker_vwma2=ticker2.vwma27;
                    }
                    
                    if (((fabs(ticker_vwma1 - ticker_vwma2) - min(ticker_vwma1,ticker_vwma2)*direction_delta > 0.00000000000000001) && (ticker_vwma2 - ticker_vwma1 < 0.00000000000000001)))
                        total_direction=1;
                    else if (((fabs(ticker_vwma1 - ticker_vwma2) - min(ticker_vwma1,ticker_vwma2)*direction_delta > 0.00000000000000001) && (ticker_vwma2 - ticker_vwma1 > 0.00000000000000001)) )
                        total_direction=-1;
                    else
                        total_direction=0;
                }
            }

            return total_direction;
        }
        
        tticker combine_multi_tickers(__global tticker *tickers_list, int start_ticker, int end_ticker, int start_time, int end_time){
            tticker total_ticker;
            int total_ticker_exists=0;
            tticker ticker;
            double min_value=20000;
            double min_time=0;
            double max_value=0;
            double max_time=0;
            double close_value=0;
 
            
            for(int ticker_number = start_ticker; ticker_number <= end_ticker; ticker_number++){
                ticker=tickers_list[ticker_number];

                if ((ticker.ticker_time > (float)start_time) && (ticker.ticker_time < (float)end_time+1)){
                    if (ticker.high_price > max_value){
                        max_value = ticker.high_price;
                        max_time = ticker.ticker_time;
                    }
                    if (ticker.low_price <min_value){
                        min_value = ticker.low_price;
                        min_time = ticker.ticker_time;
                    }
                    if (total_ticker_exists==0)
                    {
                        total_ticker_exists=1;
                        total_ticker=ticker;
                    }
                    close_value=ticker.close_price;
                    total_ticker.vwap=ticker.vwap;
                }
            }
            
            if (total_ticker_exists==0)
                return ticker;

            total_ticker.ticker_time=(float)max_time;
            total_ticker.high_price=max_value;
            total_ticker.low_price=min_value;
            total_ticker.close_price=close_value;
            total_ticker.volume=(float)min_time;
            return total_ticker;
        }
        
    double combine_multi_tickers_slide2(__global tticker *tickers_list, int start_ticker, int end_ticker, int start_time, int end_time, double stop, double take, int direction, double take_limit){
            tticker ticker;
            int total_ticker_exists=0;
            double min_value=20000;
            double max_value=0;
            double close_value=0;
            double stop_value=0;
            double take_value=0;
            double take_price=0;
            double start_value=0;
            double ticker_atrts=0;
            double tmp_take_price;
            
            for(int ticker_number = start_ticker; ticker_number <= end_ticker; ticker_number++){
                ticker=tickers_list[ticker_number];
                if (fabs(take) < 0.00000000000000001)
                    ticker_atrts=0;
                if (fabs(take - 1) < 0.00000000000000001)
                    ticker_atrts=ticker.atr1;
                if (fabs(take - 2) < 0.00000000000000001)
                    ticker_atrts=ticker.atr2;
                if (fabs (take - 3) < 0.00000000000000001)
                    ticker_atrts=ticker.atr3;
                if (fabs(take - 4) < 0.00000000000000001)
                    ticker_atrts=ticker.atr4;
                if (fabs(take - 5) < 0.00000000000000001)
                    ticker_atrts=ticker.atr5;
                if (fabs(take - 10) < 0.00000000000000001)
                    ticker_atrts=ticker.atr10;  
                
                if ((ticker.ticker_time >(float)start_time) && (ticker.ticker_time <(float)end_time+1)){
                    
                    if (total_ticker_exists==0){
                        
                        if ((take < 1) || ((direction > 0) && (ticker.low_price > ticker_atrts)) || ((direction < 0) && (ticker.high_price <ticker_atrts)))
                        {
                            total_ticker_exists=1;
                        }
                    }
                    if (total_ticker_exists!=0){
                        if (fabs(take_price) < 0.00000000000000001){
                            start_value=ticker.start_price;
                            if (direction > 0)
                                take_price=ticker.start_price*(1-stop);
                            if (direction < 0)
                                take_price=ticker.start_price*(1+stop);
                        }
                        if (ticker.high_price > max_value){
                            max_value = ticker.high_price;
                        }
                        if (ticker.low_price < min_value){
                            min_value = ticker.low_price;
                        }
                        close_value=ticker.close_price;

                        if (direction > 0)
                        {
                            if ((fabs(take_value) < 0.00000000000000001) && (fabs(stop_value) < 0.00000000000000001))
                            {
                                if ((total_ticker_exists!=0) && (take > 0) && (ticker.low_price < ticker_atrts))
                                    take_value = (ticker.close_price/start_value)-1;
    
                                if ((ticker.low_price < take_price) && (fabs(take_value) < 0.00000000000000001))
                                    take_value = (take_price/start_value)-1;
    
                                tmp_take_price = ticker.high_price*(1-(stop + take_limit)*max(0.0,1.0-(ticker.high_price-start_value)/((take_limit)*start_value)));
                                if (tmp_take_price > take_price)
                                    take_price = tmp_take_price;
                                if ((take_price> ticker.close_price) && (fabs(take_value) < 0.00000000000000001))
                                    take_value=(ticker.close_price/start_value)-1;
                            }
                            
                            if ((ticker.low_price < start_value*(1-stop)) && (fabs(take_value) < 0.00000000000000001) && (fabs(stop_value) < 0.00000000000000001))
                                stop_value = -stop;
                        }
                        else if (direction < 0)
                        {
                            if ((fabs(take_value) < 0.00000000000000001) && (fabs(stop_value) < 0.00000000000000001))
                            {
       
                                if ((total_ticker_exists!=0) && (take > 0) && (ticker.high_price > ticker_atrts))
                                    take_value = (start_value/ticker.close_price)-1;
    
                                if ((ticker.high_price > take_price) && (fabs(take_value) < 0.00000000000000001))
                                    take_value = (start_value/take_price)-1;
    
                                tmp_take_price = ticker.low_price*(1+(stop + take_limit)*max(0.0,1.0-(start_value-ticker.low_price)/((take_limit)*start_value)));
                                if (tmp_take_price < take_price)
                                    take_price = tmp_take_price;
                                if ((take_price < ticker.close_price) && (fabs(take_value) < 0.00000000000000001))
                                    take_value=(start_value/ticker.close_price)-1;
                            }
                            if ((ticker.high_price > start_value*(1+stop)) && (fabs(take_value) < 0.00000000000000001) && (fabs(stop_value) < 0.000000000000000011))
                                stop_value = -stop;
                        }
                    }
                }
            }
            
            
            if (total_ticker_exists==0)
                return 0;

            if ((fabs(take_value) > 0.00000000000000001) || (fabs(stop_value) > 0.00000000000000001))
                return stop_value+take_value;
            if (direction > 0)
                return (close_value/start_value)-1;
            if (direction < 0)
                return (start_value/close_value)-1;
            return 0;
        }
                
        double combine_multi_tickers_slide(__global tticker *tickers_list, int start_ticker, int end_ticker, int start_time, int end_time, double stop, double take, int direction, double take_limit){
            tticker ticker;
            int total_ticker_exists=0;
            double min_value=20000;
            double max_value=0;
            double close_value=0;
            double stop_value=0;
            double take_value=0;
            double take_price=0;
            double start_value=0;
            double ticker_atrts=0;
            double tmp_take_price;
            
            for(int ticker_number = start_ticker; ticker_number <= end_ticker; ticker_number++){
                ticker=tickers_list[ticker_number];
                if (fabs(take) < 0.00000000000000001)
                    ticker_atrts=0;
                if (fabs(take - 1) < 0.00000000000000001)
                    ticker_atrts=ticker.atr1;
                if (fabs(take - 2) < 0.00000000000000001)
                    ticker_atrts=ticker.atr2;
                if (fabs (take - 3) < 0.00000000000000001)
                    ticker_atrts=ticker.atr3;
                if (fabs(take - 4) < 0.00000000000000001)
                    ticker_atrts=ticker.atr4;
                if (fabs(take - 5) < 0.00000000000000001)
                    ticker_atrts=ticker.atr5;
                if (fabs(take - 10) < 0.00000000000000001)
                    ticker_atrts=ticker.atr10;  
                
                if ((ticker.ticker_time >(float)start_time) && (ticker.ticker_time <(float)end_time+1)){
                    
                    if (total_ticker_exists==0){
                        
                        if ((take < 1) || ((direction > 0) && (ticker.low_price > ticker_atrts)) || ((direction < 0) && (ticker.high_price <ticker_atrts)))
                        {
                            total_ticker_exists=1;
                        }
                    }
                    if (total_ticker_exists!=0){
                        if (fabs(take_price) < 0.00000000000000001){
                            start_value=ticker.start_price;
                            if (direction > 0)
                                take_price=ticker.start_price*(1-stop);
                            if (direction < 0)
                                take_price=ticker.start_price*(1+stop);
                        }
                        if (ticker.high_price > max_value){
                            max_value = ticker.high_price;
                        }
                        if (ticker.low_price < min_value){
                            min_value = ticker.low_price;
                        }
                        close_value=ticker.close_price;

                        if (direction > 0)
                        {
                            if ((fabs(take_value) < 0.00000000000000001) && (fabs(stop_value) < 0.00000000000000001))
                            {
                                if ((total_ticker_exists!=0) && (take > 0) && (ticker.low_price < ticker_atrts))
                                    take_value = (ticker.close_price/start_value)-1;
    
                                if ((ticker.low_price < take_price) && (fabs(take_value) < 0.00000000000000001))
                                    take_value = (take_price/start_value)-1;
    
                                tmp_take_price = ticker.high_price*(1-(stop + take_limit)*max(0.0,1.0-(ticker.high_price-start_value)/((take_limit)*start_value)));
                                if (tmp_take_price > take_price)
                                    take_price = tmp_take_price;
                                if ((take_price> ticker.close_price) && (fabs(take_value) < 0.00000000000000001))
                                    take_value=(ticker.close_price/start_value)-1;
                            }
                            
                            if ((ticker.low_price < start_value*(1-stop)) && (fabs(take_value) < 0.00000000000000001) && (fabs(stop_value) < 0.00000000000000001))
                                stop_value = -stop;
                        }
                        else if (direction < 0)
                        {
                            if ((fabs(take_value) < 0.00000000000000001) && (fabs(stop_value) < 0.00000000000000001))
                            {
       
                                if ((total_ticker_exists!=0) && (take > 0) && (ticker.high_price > ticker_atrts))
                                    take_value = (start_value/ticker.close_price)-1;
    
                                if ((ticker.high_price > take_price) && (fabs(take_value) < 0.00000000000000001))
                                    take_value = (start_value/take_price)-1;
    
                                tmp_take_price = ticker.low_price*(1+(stop + take_limit)*max(0.0,1.0-(start_value-ticker.low_price)/((take_limit)*start_value)));
                                if (tmp_take_price < take_price)
                                    take_price = tmp_take_price;
                                if ((take_price < ticker.close_price) && (fabs(take_value) < 0.00000000000000001))
                                    take_value=(start_value/ticker.close_price)-1;
                            }
                            if ((ticker.high_price > start_value*(1+stop)) && (fabs(take_value) < 0.00000000000000001) && (fabs(stop_value) < 0.000000000000000011))
                                stop_value = -stop;
                        }
                    }
                }
            }
            
            
            if (total_ticker_exists==0)
                return 0;

            if ((fabs(take_value) > 0.00000000000000001) || (fabs(stop_value) > 0.00000000000000001))
                return stop_value+take_value;
            if (direction > 0)
                return (close_value/start_value)-1;
            if (direction < 0)
                return (start_value/close_value)-1;
            return 0;
        }
        
        __kernel void analyze_by_day(__global long *tradeparam, __global tticker *tickers,  __global int *total_profit,__global double *count_profit,__global double *procn_profit,__global int *zero_days,__global int *tickers_count,__global int *begin_list,__global int *check_list,__global int *start_list,__global int *end_list,__global double *delta_list,__global double *stop_list,__global double *take_list,__global double *profit_list,__global double *comission_g,__global int *go_g)
        {
            int gid = get_global_id(0);
            int day_count=0;
            int is_up = 0;
            int day_tickers_start=0;
            int day_tickers_end=-1;
            int real_tickers_count=*tickers_count;
            double comission=*comission_g;
            int go=*go_g;
            double tmp_profit=0;
            tticker ticker1;
            total_profit[gid]=0;
            count_profit[gid]=1.0;
            procn_profit[gid]=1.0;
            zero_days[gid]=0;
            int reverse_trade;
            long tmp_param_id = tradeparam[gid];
            if (tmp_param_id > 0)
                reverse_trade=1;
            else
                reverse_trade=-1;
            tmp_param_id=tmp_param_id/reverse_trade;
            tmp_param_id=tmp_param_id/10;
            
            int check_time=check_list[tmp_param_id%100];
            tmp_param_id=tmp_param_id/100;
              
            int start_time=start_list[tmp_param_id%100];
            tmp_param_id=tmp_param_id/100;
            
            int end_time=end_list[tmp_param_id%100];
            tmp_param_id=tmp_param_id/100;
            
            double direction_delta=delta_list[tmp_param_id%10];
            tmp_param_id=tmp_param_id/10;
            
            double stop_loss=stop_list[tmp_param_id%10];
            tmp_param_id=tmp_param_id/10;
            
            double take_profit=take_list[tmp_param_id%10];
            tmp_param_id=tmp_param_id/10;
            
            double take_profit_schema=profit_list[tmp_param_id%10];
            tmp_param_id=tmp_param_id/10;
            
            int ema1 =tmp_param_id%100; 
            tmp_param_id=tmp_param_id/100;
            
            int ema2 =tmp_param_id%100; 
            tmp_param_id=tmp_param_id/100;
            
            for (int single_ticker_id = 0; single_ticker_id < real_tickers_count;single_ticker_id++)
            {
                tticker single_ticker=tickers[single_ticker_id];
                if (single_ticker.ticker_date == tickers[day_tickers_start].ticker_date)
                {
                    day_tickers_end+=1;
                }
                else
                {
                    day_count+=1;
                    if ((ema1 ==0)&&(ema2==0))
                    {
                    ticker1=combine_multi_tickers(tickers,day_tickers_start,day_tickers_end,-1,check_time);
                    is_up = is_up_direction(ticker1,check_time,direction_delta)*reverse_trade;
                    }
                    else
                    is_up = is_up_direction2(tickers,day_tickers_start,day_tickers_end,-1,check_time,direction_delta,ema1,ema2)*reverse_trade;
                    if (is_up != 0){
                        tmp_profit = combine_multi_tickers_slide(tickers,day_tickers_start,day_tickers_end,start_time,end_time,stop_loss,take_profit,is_up,take_profit_schema);

                        if (tmp_profit>0)                             
                            total_profit[gid]+=1;
                        else if (tmp_profit<0)
                            total_profit[gid]-=1;
                        if (fabs(tmp_profit)> 0.00000000000000001)
                            tmp_profit-=comission/go;
                        else
                            zero_days[gid]+=1;
                        count_profit[gid]=count_profit[gid]+tmp_profit*go;
                        //count_profit[gid]=combine_multi_tickers_slide2(tickers,day_tickers_start,day_tickers_end,start_time,end_time,stop_loss,take_profit,is_up,take_profit_schema);
                        procn_profit[gid]=procn_profit[gid]*(1+tmp_profit*go);
                    }
                    else{
                        zero_days[gid]+=1;

                    }
                    day_tickers_start=single_ticker_id;
                    day_tickers_end=single_ticker_id;
                }
            }
            day_count+=1;
            //day_tickers_end-=1;
            if ((ema1 ==0)&&(ema2==0))
            {
            ticker1=combine_multi_tickers(tickers,day_tickers_start,day_tickers_end,-1,check_time);
            is_up = is_up_direction(ticker1,check_time,direction_delta)*reverse_trade;
            }
            else
            is_up = is_up_direction2(tickers,day_tickers_start,day_tickers_end,-1,check_time,direction_delta,ema1,ema2)*reverse_trade;
            if (is_up != 0){
                tmp_profit = combine_multi_tickers_slide(tickers,day_tickers_start,day_tickers_end,start_time,end_time,stop_loss,take_profit,is_up,take_profit_schema);
                if (tmp_profit>0)                             
                    total_profit[gid]+=1;
                else if (tmp_profit<0)
                    total_profit[gid]-=1;
                if (fabs(tmp_profit) > 0.00000000000000001)
                    tmp_profit-=comission/go;
                else
                    zero_days[gid]+=1;
                count_profit[gid]=count_profit[gid]+tmp_profit*go;
                //count_profit[gid]=check_time;//combine_multi_tickers_slide2(tickers,day_tickers_start,day_tickers_end,start_time,end_time,stop_loss,take_profit,is_up,take_profit_schema,);
                procn_profit[gid]=procn_profit[gid]*(1+tmp_profit*go);
                //procn_profit[gid]=combine_multi_tickers_slide2(tickers,day_tickers_start,day_tickers_end,start_time,end_time,stop_loss,take_profit,is_up,take_profit_schema);
            }
            else{
                zero_days[gid]+=1;

            }
        }
        
                
        """
        self.prg = cl.Program(self.ctx, self.main_code).build()
        
        self.adv_code="""
        
        typedef struct{
            long best_tp;
            int best_ind;
        }bestpair;
        
        bestpair getbesttp(__global long *tradeparam, __global double *procn_profit, int max_tp){
            bestpair besttp;
            long curr_tp;
            double max_prof=0;
            for (int i =0;i<max_tp;i++){
                curr_tp=tradeparam[i];
                if (curr_tp > 0)
                {
                    //main_check=curr_tp%1000;
                    //main_ema=curr_tp/10000000000;
                    //if ((main_check == check)&&(main_ema==ema))
                    //{
                        if (procn_profit[i] > max_prof)
                        {
                            max_prof=procn_profit[i];
                            besttp.best_tp=curr_tp;
                            besttp.best_ind=i;
                        }
                    //}
                }
            }
            return besttp;
        }
        
        __kernel void analyze_tradeparam(__global long *tradeparam,__global double *procn_profit,__global int *trade_param_count,__global int *best_indexes)
        {
            int gid = get_global_id(0);
            long main_tp=tradeparam[gid];
            best_indexes[gid]=0;
            int main_sign=main_tp/abs(main_tp);
            if (main_tp < 0)
            {
                main_tp=-main_tp;
                int real_trade_param_count=*trade_param_count;
                long tp_candidate=-1;
                double max_profit=-1.0;
                bestpair besttp=getbesttp(tradeparam,procn_profit,real_trade_param_count);
                best_indexes[gid]=besttp.best_ind;          
            }
        }
        """
        
        self.prg2 = cl.Program(self.ctx2, self.adv_code).build()
    
    def _unpack_trade_param(self,tmp_test_params):
        if tmp_test_params > 0:
            trade = 1
        else:
            trade = -1
        tmp_test_params=tmp_test_params/trade
        begin=tmp_test_params%10
        tmp_test_params=tmp_test_params/10

        check=tmp_test_params%100
        tmp_test_params=tmp_test_params/100

        start=tmp_test_params%100
        tmp_test_params=tmp_test_params/100

        end=tmp_test_params%100
        tmp_test_params=tmp_test_params/100

        direction_delta=tmp_test_params%10
        tmp_test_params=tmp_test_params/10

        stop_loss=tmp_test_params%10
        tmp_test_params=tmp_test_params/10
        
        take=tmp_test_params%10
        tmp_test_params=tmp_test_params/10

        method=tmp_test_params%10
        tmp_test_params=tmp_test_params/10
        
        ema1=tmp_test_params%100
        tmp_test_params=tmp_test_params/100
        
        ema2=tmp_test_params%100
        tmp_test_params=tmp_test_params/100
        return [begin,check,start,end,direction_delta,stop_loss,take,method,ema1,ema2,trade]
        
    def _compare_two_params(self,tradeparam1,tradeparam2):
        #unpack_param1=self._unpack_trade_param(tradeparam1)
        #unpack_param2=self._unpack_trade_param(tradeparam2)

        if not tradeparam1 % 1000 == tradeparam2 % 1000:
            return False
        if not tradeparam1 / 10000000000 == tradeparam2 / 10000000000:
            return False       
        #for ind_to_comp in compare_indexes:
        #    if not unpack_param1[ind_to_comp] == unpack_param2[ind_to_comp]:
        #        same = False
        return True
        
    def main_analyzer_cl(self,tradeparam_list,limit):
        tradeparam_list=np.array(tradeparam_list,dtype=np.int64)
        tradeparam_g =  cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=tradeparam_list)
        results_days=[]
        param_len=len(tradeparam_list)

        total_profit =  np.empty_like(tradeparam_list.astype(np.int32))

        count_profit =np.empty_like(tradeparam_list.astype(np.float64))

        procn_profit = np.empty_like(tradeparam_list.astype(np.float64))

        zero_days = np.empty_like(tradeparam_list.astype(np.int32))

        total_profit_g = cl.Buffer(self.ctx, self.mf.WRITE_ONLY| self.mf.COPY_HOST_PTR, hostbuf=total_profit)
        count_profit_g = cl.Buffer(self.ctx, self.mf.WRITE_ONLY| self.mf.COPY_HOST_PTR, hostbuf=count_profit)
        procn_profit_g = cl.Buffer(self.ctx, self.mf.WRITE_ONLY| self.mf.COPY_HOST_PTR, hostbuf=procn_profit)
        zero_days_g = cl.Buffer(self.ctx, self.mf.WRITE_ONLY| self.mf.COPY_HOST_PTR, hostbuf=zero_days)
        exec_evt = self.prg.analyze_by_day(self.queue, tradeparam_list.shape, None, tradeparam_g, self.tickers_g, total_profit_g, count_profit_g, procn_profit_g, zero_days_g,self.height_g,self.begin_list_g,self.check_list_g,self.start_list_g,self.end_list_g,self.delta_list_g,self.stop_list_g,self.take_list_g,self.profit_list_g,self.comission_g,self.go_g)
        exec_evt.wait()
        del tradeparam_g
        cl.enqueue_copy(self.queue, total_profit, total_profit_g).wait()
        cl.enqueue_copy(self.queue, count_profit, count_profit_g).wait()
        cl.enqueue_copy(self.queue, procn_profit, procn_profit_g).wait()
        cl.enqueue_copy(self.queue, zero_days, zero_days_g).wait()
        #total_profit_g.clear()
        del total_profit_g
        del count_profit_g
        del procn_profit_g
        del zero_days_g
        #best_indexes=[]
        #for i in range(param_len*10):
        #    best_indexes.append(0.1)
        #best_indexes=np.array(best_indexes)
        best_indexes =  np.empty_like(tradeparam_list.astype(np.int32))
        trade_param_count_g = cl.Buffer(self.ctx2, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=np.int32(param_len))
        procn_profit_g =  cl.Buffer(self.ctx2, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=np.array(procn_profit,dtype=np.float64))
        tradeparam_g =  cl.Buffer(self.ctx2, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=tradeparam_list)
        best_indexes_g = cl.Buffer(self.ctx2, self.mf.WRITE_ONLY | self.mf.COPY_HOST_PTR, hostbuf=best_indexes)
        if not best_indexes_g:
            print "FAILED TO CREATE BUFFER"
        exec_evt = self.prg2.analyze_tradeparam(self.queue2, tradeparam_list.shape, None, tradeparam_g, procn_profit_g,trade_param_count_g,best_indexes_g)
        exec_evt.wait()
        cl.enqueue_copy(self.queue2, best_indexes, best_indexes_g).wait()
        del best_indexes_g
        del trade_param_count_g
        del procn_profit_g
        del tradeparam_g 
        for i in range(param_len):
            #if i < 0:
            #j=1
            j=best_indexes[i]
            if j >0:
                results_days.append([procn_profit[i]*procn_profit[j],tradeparam_list[i],total_profit[i]+total_profit[j]-1,count_profit[i]+count_profit[j]-1,tradeparam_list[j]])
            else:
                results_days.append([procn_profit[i],tradeparam_list[i],total_profit[i],count_profit[i]])
                        
        del total_profit
        del count_profit
        del procn_profit

        del tradeparam_list
        del exec_evt
        results_days.sort()
         
        return results_days[-limit:]