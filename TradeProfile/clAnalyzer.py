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
         
        # Create queue for each kernel execution
        self.queue = cl.CommandQueue(self.ctx)
         
        self.mf = cl.mem_flags
        self.tickers_g =  cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=np.array(tickers,dtype=np.float32))
        self.begin_list_g =  cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=np.array(begin_list,dtype=np.int32))
        self.check_list_g =  cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=np.array(check_list,dtype=np.int32))
        self.start_list_g =  cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=np.array(start_list,dtype=np.int32))
        self.end_list_g =  cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=np.array(end_list,dtype=np.int32))
        self.delta_list_g =  cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=np.array(delta_list,dtype=np.float32))
        self.stop_list_g =  cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=np.array(stop_list,dtype=np.float32))
        self.take_list_g =  cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=np.array(take_list,dtype=np.float32))
        self.profit_list_g =  cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=np.array(profit_list,dtype=np.float32))
        
        self.height_g = cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=np.int32(len(tickers)))
        
        self.comission_g = cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR , hostbuf=np.float32(comission))
        self.go_g = cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=np.int32(go))
        self.main_code= """

        typedef struct{
            float atr;
            float atr1;
            float atr15;
            float atr2;
            float atr3;
            float atr4;
            float atr5;
            float atr10;
        } tindicator;  
          
          
        typedef struct{
            float ticker_name;
            float ticker_interval;
            float ticker_date;
            float ticker_time;
            float start_price;
            float high_price;
            float low_price;
            float close_price;
            float volume;
            float atr;
            float atr1;
            float atr15;
            float atr2;
            float atr3;
            float atr4;
            float atr5;
            float atr10;
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
        
        int is_up_direction(tticker ticker1, int check_time, float direction_delta){
            
            if ((fabs(ticker1.start_price - ticker1.close_price) - min(ticker1.start_price,ticker1.close_price)*direction_delta > 0.000001) && (ticker1.start_price - ticker1.close_price < 0.000001))
                return 1;
            else if ((fabs(ticker1.start_price - ticker1.close_price) - min(ticker1.start_price,ticker1.close_price)*direction_delta > 0.000001) && (ticker1.start_price - ticker1.close_price > 0.000001))
                return -1;
            else
                return 0;
        }
        
        tticker combine_multi_tickers(__global tticker *tickers_list, int start_ticker, int end_ticker, int start_time, int end_time){
            tticker total_ticker;
            int total_ticker_exists=0;
            tticker ticker;
            float min_value=20000;
            float min_time=0;
            float max_value=0;
            float max_time=0;
            float close_value=0;
 
            
            for(int ticker_number = start_ticker; ticker_number <= end_ticker; ticker_number++){
                ticker=tickers_list[ticker_number];

                if ((ticker.ticker_time - (float)start_time > 0.000001) && (ticker.ticker_time - (float)end_time <= 0.000001)){
                    if (ticker.high_price - max_value > 0.000001){
                        max_value = ticker.high_price;
                        max_time = ticker.ticker_time;
                    }
                    if (ticker.low_price - min_value < 0.000001){
                        min_value = ticker.low_price;
                        min_time = ticker.ticker_time;
                    }
                    if (total_ticker_exists==0)
                    {
                        total_ticker_exists=1;
                        total_ticker=ticker;
                    }
                    close_value=ticker.close_price;
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
        
        float combine_multi_tickers_slide2(__global tticker *tickers_list, int start_ticker, int end_ticker, int start_time, int end_time, float stop, float take, int direction, float take_limit){
            tticker ticker;
            int total_ticker_exists=0;
            float min_value=20000;
            float max_value=0;
            float close_value=0;
            float stop_value=0;
            float take_value=0;
            float take_price=0;
            float start_value=0;
            float ticker_atrts=0;
            float tmp_take_price;
            
            for(int ticker_number = start_ticker; ticker_number <= end_ticker; ticker_number++){
                ticker=tickers_list[ticker_number];
                if (take < 0.000001)
                    ticker_atrts=0;
                if ((take > 0.000001) && (take - 1 < 0.000001))
                    ticker_atrts=ticker.atr1;
                if ((take - 1 > 0.000001) && (take - 2 < 0.000001))
                    ticker_atrts=ticker.atr2;
                if ((take - 2 > 0.000001) && (take - 3 < 0.000001))
                    ticker_atrts=ticker.atr3;
                if ((take - 3 > 0.000001) && (take - 4 < 0.000001))
                    ticker_atrts=ticker.atr4;
                if ((take - 4 > 0.000001) && (take - 5 < 0.000001))
                    ticker_atrts=ticker.atr5;
                if ((take - 5 > 0.000001) && (take - 10 < 0.000001))
                    ticker_atrts=ticker.atr10;  
                
                if ((ticker.ticker_time - (float)start_time > 0.000001) && (ticker.ticker_time - (float)end_time <= 0.000001)){
                    
                    if (total_ticker_exists==0){
                        
                        if ((take < 1) || ((direction > 0) && (ticker.low_price - ticker_atrts > 0.000001)) || ((direction < 0) && (ticker.high_price - ticker_atrts < 0.000001)))
                        {
                            total_ticker_exists=1;
                        }
                    }
                    if (total_ticker_exists!=0){
                        if ((take_price < 0.000001) && (take_price > -0.000001)){
                            start_value=ticker.start_price;
                            if (direction > 0)
                                take_price=ticker.start_price*(1-stop);
                            if (direction < 0)
                                take_price=ticker.start_price*(1+stop);
                        }
                        if (ticker.high_price - max_value > 0.000001){
                            max_value = ticker.high_price;
                        }
                        if (ticker.low_price - min_value < 0.000001){
                            min_value = ticker.low_price;
                        }
                        close_value=ticker.close_price;

                        if (direction > 0)
                        {
                            if ((take_value < 0.000001) && (stop_value < 0.000001) && (take_value > -0.000001) && (stop_value > -0.000001))
                            {
                                if ((total_ticker_exists!=0) && (take > 0) && (ticker.low_price - ticker_atrts < 0.000001))
                                    take_value = (ticker.close_price/start_value)-1;
    
                                if ((ticker.low_price - take_price < 0.000001) && (take_value < 0.000001) && (take_value > -0.000001))
                                    take_value = (take_price/start_value)-1;
    
                                tmp_take_price = ticker.high_price*(1-(stop + take_limit)*max(0.000001,1.000001-(ticker.high_price-start_value)/((take_limit)*start_value)));
                                if (tmp_take_price - take_price > 0.000001)
                                    take_price = tmp_take_price;
                                if ((take_price - ticker.close_price > 0.000001) && (take_value < 0.000001) && (take_value > -0.000001))
                                    take_value=(ticker.close_price/start_value)-1;
                            }
                            
                            if ((ticker.low_price - start_value*(1-stop) < 0.000001) && (take_value < 0.000001) && (stop_value < 0.000001) && (take_value > -0.000001) && (stop_value > -0.000001))
                                stop_value = -stop;
                        }
                        else if (direction < 0)
                        {
                            if ((take_value < 0.000001) && (stop_value < 0.000001) && (take_value > -0.000001) && (stop_value > -0.000001))
                            {
       
                                if ((total_ticker_exists!=0) && (take > 0) && (ticker.high_price - ticker_atrts > 0.000001))
                                    take_value = (start_value/ticker.close_price)-1;
    
                                if ((ticker.high_price - take_price > 0.000001) && (take_value < 0.000001) && (take_value > -0.000001))
                                    take_value = (start_value/take_price)-1;
    
                                tmp_take_price = ticker.low_price*(1+(stop + take_limit)*max(0.000001,1.000001-(start_value-ticker.low_price)/((take_limit)*start_value)));
                                if (tmp_take_price - take_price < 0.000001)
                                    take_price = tmp_take_price;
                                if ((take_price - ticker.close_price < 0.000001) && (take_value < 0.000001) && (take_value > -0.000001))
                                    take_value=(start_value/ticker.close_price)-1;
                            }
                            if ((ticker.high_price - start_value*(1+stop) > 0.000001) && (take_value < 0.000001) && (stop_value < 0.000001) && (take_value > -0.000001) && (stop_value > -0.000001))
                                stop_value = -stop;
                        }
                    }
                }
            }
            
            
            if (total_ticker_exists==0)
                return 0;

            if ((take_value > 0.000001) || (stop_value > 0.000001) || (take_value < -0.000001) || (stop_value < -0.000001))
                return stop_value+take_value;
            if (direction > 0)
                return (close_value/start_value)-1;
            if (direction < 0)
                return ticker.ticker_time;//(start_value/close_value)-1;
            return 0;
        }
                
        float combine_multi_tickers_slide(__global tticker *tickers_list, int start_ticker, int end_ticker, int start_time, int end_time, float stop, float take, int direction, float take_limit){
            tticker ticker;
            int total_ticker_exists=0;
            float min_value=20000;
            float max_value=0;
            float close_value=0;
            float stop_value=0;
            float take_value=0;
            float take_price=0;
            float start_value=0;
            float ticker_atrts=0;
            float tmp_take_price;
            
            for(int ticker_number = start_ticker; ticker_number <= end_ticker; ticker_number++){
                ticker=tickers_list[ticker_number];
                if (take < 0.000001)
                    ticker_atrts=0;
                if ((take > 0.000001) && (take - 1 < 0.000001))
                    ticker_atrts=ticker.atr1;
                if ((take - 1 > 0.000001) && (take - 2 < 0.000001))
                    ticker_atrts=ticker.atr2;
                if ((take - 2 > 0.000001) && (take - 3 < 0.000001))
                    ticker_atrts=ticker.atr3;
                if ((take - 3 > 0.000001) && (take - 4 < 0.000001))
                    ticker_atrts=ticker.atr4;
                if ((take - 4 > 0.000001) && (take - 5 < 0.000001))
                    ticker_atrts=ticker.atr5;
                if ((take - 5 > 0.000001) && (take - 10 < 0.000001))
                    ticker_atrts=ticker.atr10;  
                
                if ((ticker.ticker_time - (float)start_time > 0.000001) && (ticker.ticker_time - (float)end_time <= 0.000001)){
                    
                    if (total_ticker_exists==0){
                        
                        if ((take < 1) || ((direction > 0) && (ticker.low_price - ticker_atrts > 0.000001)) || ((direction < 0) && (ticker.high_price - ticker_atrts < 0.000001)))
                        {
                            total_ticker_exists=1;
                        }
                    }
                    if (total_ticker_exists!=0){
                        if ((take_price < 0.000001) && (take_price > -0.000001)){
                            start_value=ticker.start_price;
                            if (direction > 0)
                                take_price=ticker.start_price*(1-stop);
                            if (direction < 0)
                                take_price=ticker.start_price*(1+stop);
                        }
                        if (ticker.high_price - max_value > 0.000001){
                            max_value = ticker.high_price;
                        }
                        if (ticker.low_price - min_value < 0.000001){
                            min_value = ticker.low_price;
                        }
                        close_value=ticker.close_price;

                        if (direction > 0)
                        {
                            if ((take_value < 0.000001) && (stop_value < 0.000001) && (take_value > -0.000001) && (stop_value > -0.000001))
                            {
                                if ((total_ticker_exists!=0) && (take > 0) && (ticker.low_price - ticker_atrts < 0.000001))
                                    take_value = (ticker.close_price/start_value)-1;
    
                                if ((ticker.low_price - take_price < 0.000001) && (take_value < 0.000001) && (take_value > -0.000001))
                                    take_value = (take_price/start_value)-1;
    
                                tmp_take_price = ticker.high_price*(1-(stop + take_limit)*max(0.000001,1.000001-(ticker.high_price-start_value)/((take_limit)*start_value)));
                                if (tmp_take_price - take_price > 0.000001)
                                    take_price = tmp_take_price;
                                if ((take_price - ticker.close_price > 0.000001) && (take_value < 0.000001) && (take_value > -0.000001))
                                    take_value=(ticker.close_price/start_value)-1;
                            }
                            
                            if ((ticker.low_price - start_value*(1-stop) < 0.000001) && (take_value < 0.000001) && (stop_value < 0.000001) && (take_value > -0.000001) && (stop_value > -0.000001))
                                stop_value = -stop;
                        }
                        else if (direction < 0)
                        {
                            if ((take_value < 0.000001) && (stop_value < 0.000001) && (take_value > -0.000001) && (stop_value > -0.000001))
                            {
       
                                if ((total_ticker_exists!=0) && (take > 0) && (ticker.high_price - ticker_atrts > 0.000001))
                                    take_value = (start_value/ticker.close_price)-1;
    
                                if ((ticker.high_price - take_price > 0.000001) && (take_value < 0.000001) && (take_value > -0.000001))
                                    take_value = (start_value/take_price)-1;
    
                                tmp_take_price = ticker.low_price*(1+(stop + take_limit)*max(0.000001,1.000001-(start_value-ticker.low_price)/((take_limit)*start_value)));
                                if (tmp_take_price - take_price < 0.000001)
                                    take_price = tmp_take_price;
                                if ((take_price - ticker.close_price < 0.000001) && (take_value < 0.000001) && (take_value > -0.000001))
                                    take_value=(start_value/ticker.close_price)-1;
                            }
                            if ((ticker.high_price - start_value*(1+stop) > 0.000001) && (take_value < 0.000001) && (stop_value < 0.000001) && (take_value > -0.000001) && (stop_value > -0.000001))
                                stop_value = -stop;
                        }
                    }
                }
            }
            
            
            if (total_ticker_exists==0)
                return 0;

            if ((take_value > 0.000001) || (stop_value > 0.000001) || (take_value < -0.000001) || (stop_value < -0.000001))
                return stop_value+take_value;
            if (direction > 0)
                return (close_value/start_value)-1;
            if (direction < 0)
                return (start_value/close_value)-1;
            return 0;
        }
        
        __kernel void analyze_by_day(__global long *tradeparam, __global tticker *tickers,  __global int *total_profit,__global float *count_profit,__global float *procn_profit,__global int *zero_days,__global int *tickers_count,__global int *begin_list,__global int *check_list,__global int *start_list,__global int *end_list,__global float *delta_list,__global float *stop_list,__global float *take_list,__global float *profit_list,__global float *comission_g,__global int *go_g)
        {
            int gid = get_global_id(0);
            int day_count=0;
            int is_up = 0;
            int day_tickers_start=0;
            int day_tickers_end=-1;
            int real_tickers_count=*tickers_count;
            float comission=*comission_g;
            int go=*go_g;
            float tmp_profit=0;
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
            
            float direction_delta=delta_list[tmp_param_id%10];
            tmp_param_id=tmp_param_id/10;
            
            float stop_loss=stop_list[tmp_param_id%10];
            tmp_param_id=tmp_param_id/10;
            
            float take_profit=take_list[tmp_param_id%10];
            tmp_param_id=tmp_param_id/10;
            
            float take_profit_schema=profit_list[tmp_param_id%10];
            
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
                    ticker1=combine_multi_tickers(tickers,day_tickers_start,day_tickers_end,-1,check_time);
                    is_up = is_up_direction(ticker1,check_time,direction_delta)*reverse_trade;
                    if (is_up != 0){
                        tmp_profit = combine_multi_tickers_slide(tickers,day_tickers_start,day_tickers_end,start_time,end_time,stop_loss,take_profit,is_up,take_profit_schema);

                        if (tmp_profit>0.0000000001)                             
                            total_profit[gid]+=1;
                        else if (tmp_profit<-0.0000000001)
                            total_profit[gid]-=1;
                        if ((tmp_profit < -0.0000000001) || (tmp_profit > 0.0000000001))
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
            ticker1=combine_multi_tickers(tickers,day_tickers_start,day_tickers_end,-1,check_time);
            
            is_up = is_up_direction(ticker1,check_time,direction_delta)*reverse_trade;
            if (is_up != 0){
                tmp_profit = combine_multi_tickers_slide(tickers,day_tickers_start,day_tickers_end,start_time,end_time,stop_loss,take_profit,is_up,take_profit_schema);
                if (tmp_profit>0.0000000001)                             
                    total_profit[gid]+=1;
                else if (tmp_profit<-0.0000000001)
                    total_profit[gid]-=1;
                if ((tmp_profit < -0.0000000001) || (tmp_profit > 0.0000000001))
                    tmp_profit-=comission/go;
                else
                    zero_days[gid]+=1;
                count_profit[gid]=count_profit[gid]+tmp_profit*go;
                //count_profit[gid]=tmp_profit;//combine_multi_tickers_slide2(tickers,day_tickers_start,day_tickers_end,start_time,end_time,stop_loss,take_profit,is_up,take_profit_schema,);
                procn_profit[gid]=procn_profit[gid]*(1+tmp_profit*go);
                //procn_profit[gid]=combine_multi_tickers_slide2(tickers,day_tickers_start,day_tickers_end,start_time,end_time,stop_loss,take_profit,is_up,take_profit_schema);
            }
            else{
                zero_days[gid]+=1;

            }
        }
        """
        self.prg = cl.Program(self.ctx, self.main_code).build()
        
    def main_analyzer_cl(self,tradeparam_list,limit):
        tradeparam_list=np.array(tradeparam_list,dtype=np.int64)
        tradeparam_g =  cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=tradeparam_list)
        tmp_list=[]
        results_days=[]
        param_len=len(tradeparam_list)

        total_profit =  np.empty_like(tradeparam_list.astype(np.int32))

        count_profit =np.empty_like(tradeparam_list.astype(np.float32))

        procn_profit = np.empty_like(tradeparam_list.astype(np.float32))

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
        
        for i in range(param_len):
            results_days.append([procn_profit[i][0],tradeparam_list[i][0],total_profit[i][0],count_profit[i][0]])
        del tmp_list
        del total_profit
        del count_profit
        del procn_profit
        del total_profit_g
        del count_profit_g
        del zero_days_g
        del tradeparam_list
        del exec_evt
        results_days.sort()
         
        return results_days[-limit:]