'''
Created on 6 Jan 2018

Test module neuron network trade analyzer

@author: Kurliana
'''

import numpy
from ProfileAnalyzerTest import ProfileAnalyser
import keras
import os
from keras.models import Sequential
from keras.layers import Dense, Dropout
from copy import deepcopy

class NNTrader():
    
    def __init__(self, model_path = "nn_trade_test_model.h5"):
        print "Start model loading"
        self.model_path =model_path
        self.model=keras.models.load_model(model_path)
        print "Stop model loading"
        self.predict_size=6
        self.num_classes=2
       
    def convert_to_comp_array(self,ticker,direction):
        comp_array=[]
        comp_array.append((ticker[4]-ticker[7])/abs(ticker[7]))
        comp_array.append((ticker[5]-ticker[7])/abs(ticker[7]))
        comp_array.append((ticker[6]-ticker[7])/abs(ticker[7]))
        #comp_array.append((ticker[5]-ticker[4])/abs(ticker[7]))
        #comp_array.append((ticker[6]-ticker[4])/abs(ticker[7]))
        #comp_array.append((ticker[9]["VWMA9"]-ticker[9]["VWMA20"])/abs(ticker[7]))
        #comp_array.append((ticker[9]["VWMA9"]-ticker[7])/abs(ticker[7]))
        comp_array.append((ticker[9]["EVWMA9"]-ticker[9]["EVWMA20"])/abs(ticker[7]))
        #comp_array.append((ticker[9]["MININD"]-ticker[9]["MAXIND"])/abs(ticker[7]))
        #comp_array.append((ticker[9]["ATR"])/abs(ticker[7]))
        comp_array.append(direction)
        return comp_array
        
    def prepare_data(self,data_file,mode="rus"):
        predict_size=6
        num_classes=2
        self.pa = ProfileAnalyser(data_file,mode=mode)
        self.day_tickers = self.pa.filter_tickers(self.pa.tickers, self.pa.begin_time,self.pa.max_time-1000,-1,-1)
        self.pa.tickers = self.day_tickers
        
        self.x_total=[]
        self.y_total=[]
        self.x_train=[]
        self.y_train=[]
        self.x_test=[]
        self.y_test=[]
        
        for ind in range(len(self.pa.tickers)):
            i = self.pa.tickers[ind]
        
            self.x_total.append(self.convert_to_comp_array(i,self.pa.best_directions[ind]))
        
            #x_total.append(convert_to_comp_array(i))
            #x_total.append([abs(i[4]-i[7])/i[7],abs(i[5]-i[7])/i[7],abs(i[7]-i[6])/i[7]])
            #for param_name in i[9].keys():
            #    x_total[-1].append(i[9][param_name])
            if self.pa.best_directions[ind] > 0:
                self.y_total.append(self.pa.best_directions[ind])
            elif self.pa.best_directions[ind] < 0:
                self.y_total.append(0)
            elif self.pa.best_directions[ind] == 0:
                self.y_total.append(2)
        
        #log.info(x_total[-2:])
        x_total=numpy.array(self.x_total,dtype=object)
        #log.info(x_total[-2:])
        
        for ind in range(len(self.pa.tickers)): 
            if ind > self.predict_size-1 and ind <= len(x_total)*7/10:
                self.x_train.append(deepcopy(x_total[ind-predict_size:ind]))
                self.x_train[-1][-1][-1]=(self.pa.tickers[ind-predict_size][4]-self.pa.tickers[ind][7])/self.pa.tickers[ind][7]
                #log.info(x_total[ind-predict_size:ind])
                #x_train[-1].append()
                self.y_train.append(self.y_total[ind])
                #x_train[-1]+=pa.best_directions[ind-6:ind]#+pa.best_directions[ind+1:ind+3]
                #print "AFTER"
                #print x_train[-1]
                #x_train[-1][-5][-2] = 0
                #x_train.append(x_total[ind])
        
        
            elif ind > len(x_total)*7/10 and ind < len(x_total): #and ind < len(x_total)*5/10:
                self.x_test.append(deepcopy(x_total[ind-predict_size:ind]))
                self.x_test[-1][-1][-1]=(self.pa.tickers[ind-predict_size][4]-self.pa.tickers[ind][7])/self.pa.tickers[ind][7]
                self.y_test.append(self.y_total[ind])
                #x_test[-1]+=pa.best_directions[ind-6:ind]#+pa.best_directions[ind+1:ind+3]
                #x_test[-1][-5][-2] = 0
        
        x_train=numpy.array(self.x_train)
        x_test=numpy.array(self.x_test)
        x_train = x_train.reshape(len(x_train),len(x_total[0])*self.predict_size)
        x_test = x_test.reshape(len(x_test),len(x_total[0])*self.predict_size)
        y_train=numpy.array(self.y_train)
        y_test=numpy.array(self.y_test)
        #x_train = x_train.astype('float32')
        #x_test = x_test.astype('float32')
        y_train = keras.utils.to_categorical(y_train,num_classes=self.num_classes)
        y_test = keras.utils.to_categorical(y_test,num_classes=self.num_classes)
        self.pa.best_directions=[]

    def get_last_direction(self):
        new_best_directions=[1,1,1,1,1,1]
        
        for ind in range(len(self.pa.tickers)):
            x_check=[]
            if ind >= self.predict_size:
                x_check.append(deepcopy(self.x_total[ind-self.predict_size:ind]))
                x_check[-1][-1][-1]=(self.pa.tickers[ind-self.predict_size][4]-self.pa.tickers[ind][7])/self.pa.tickers[ind][7]
                for j in range(2,1,self.predict_size+1):
                    x_check[-1][-j][-1]=new_best_directions[-j+1]
                x_check1=numpy.array(x_check[-1])
                x_check1=x_check1.reshape(1,self.predict_size*len(self.x_total[0]))
                predict = self.model.predict(x_check1)
                #if ind == 26:
                #    print predict,ind
                #    print new_best_directions[-6:]
                #    print self.x_total[ind]
                if predict[0][0] > predict[0][1]:
                    new_best_directions.append(-1)
                else:
                    new_best_directions.append(1)
            
        if not len(self.x_total) == len(new_best_directions):
            print "ERROR: tickers %s and directions %s" % (len(self.x_total),len(new_best_directions))
        
        self.pa.best_directions=new_best_directions
        
        day_ranges={0:[10000, 10000, 10000,  230000, 1, 0, 0.04, 1, 'simple_0.04', 9, 20],
                    1:[100000, 115000, 125000, 170000, 1, 0, 0.04, 1, 'take_innsta_0.01', 9, 20],
                    2:[100000, 102000, 134000, 174000, -1, 0, 0.04, 1, 'take_innsta_0.03', 9, 20],
                    3:[100000, 112000, 121000, 175000, 1, 0, 0.04, 1, 'take_innsta_0.03', 9, 0],
                    4:[100000, 102000, 104000, 172000, 1, 0, 0.04, 0, 'take_innsta_0.015', 14, 27],
                    5:[183000, 183000, 183000, 183000,1],
                    6:[183000, 183000, 183000, 183000,1]}
        begin_time,check_time,start_time,end_time,trade,delta,stop,take,method,ema1,ema2 = day_ranges[0][:11]
        total_profit, count_profit, procn_profit, list_profit, zero_days = self.pa.analyze_by_day2(self.day_tickers, check_time,start_time,end_time, 0,  delta, stop, take,True,method,ema1,ema2)
        print total_profit, count_profit, procn_profit, zero_days
        #print new_best_directions
        return new_best_directions
    
    def check_correct_prediction(self):
        prv_best_directions=[1,1,1,1,1,1]
        prev_x_check=[]
        x_check=[]
        for last_ind in range(len(self.pa.tickers)+1):
            new_best_directions=[1,1,1,1,1,1]
            x_total1=self.x_total[:last_ind]
            for ind in range(last_ind):
                x_check=[]
                if ind >= self.predict_size:
                    x_check.append(deepcopy(x_total1[ind-self.predict_size:ind]))
                    x_check[-1][-1][-1]=(self.pa.tickers[ind-self.predict_size][4]-self.pa.tickers[ind][7])/self.pa.tickers[ind][7]
                    for j in range(2,1,self.predict_size+1):
                        x_check[-1][-j][-1]=new_best_directions[-j+1]
                    x_check1=numpy.array(x_check[-1])
                    x_check1=x_check1.reshape(1,self.predict_size*len(x_total1[0]))
                    predict = self.model.predict(x_check1)
                    #if ind == 26:
                    #    print predict,ind
                    #    print new_best_directions[-6:]
                    #    print self.x_total[ind]
                    if predict[0][0] > predict[0][1]:
                        new_best_directions.append(-1)
                    else:
                        new_best_directions.append(1)
                    for check_ind in range(len(new_best_directions)-1):
                        if new_best_directions[check_ind] != prv_best_directions[check_ind]:
                            print "ERROR: Diff element %s with max %s with ticker" % (check_ind,last_ind)
                            #print x_check[-3:]
                    #print prev_x_check[-2:]
                    #exit(0)
            try:
                if len(prev_x_check) > 0 and len(x_check) > 1 and  not numpy.array_equal(prev_x_check,numpy.array(x_check[:-1])):
                    print 'ERROR: the difference =', numpy.subtract(prev_x_check,numpy.array(x_check[:-1]))
            except Exception as e:
                print e
                print "BEFORE"
                print prev_x_check
                print "AFTER"
                print x_check
                exit(0)
            if len(x_check) > 0:
                prev_x_check=x_check    
            prv_best_directions=new_best_directions
            #print prv_best_directions
   
if __name__ == "__main__":
    nnt = NNTrader(model_path = "nn_trade_test_model.h5",init_model = False)
    try:
        for filename in os.listdir("./"):#os.listdir("C:\\Just2Trade Client\\"):
            if filename.find("150105_170801") >= 0 and filename.find("tickers_BTCUSD") !=0:
                nnt.prepare_data("FEES_150105_170801.txt","world")
                print filename
                #nnt.prepare_data("C:\\Just2Trade Client\\tickers_BTCUSD3.txt","world")
                nnt.get_last_direction()
                nnt.check_correct_prediction()
                exit(0)
    except Exception as e:
        print e