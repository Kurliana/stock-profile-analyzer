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

class NNTrader():
    
    def __init__(self, model_path = "nn_trade_test_model.h5", init_model = True):
        print "Start model loading"
        if init_model:
            self.prepare_data("FEES_150105_170801.txt.",mode="rus")
            self.init_model()
        else:
            self.model_path =model_path
            self.model=keras.models.load_model(model_path)
        print "Stop model loading"
        
    def init_model(self):
        self.model = Sequential()
        self.model.add(Dense(51, activation='tanh', input_shape=(6*len(self.x_total[0]),)))
        self.model.add(Dropout(0.2))
        self.model.add(Dense(51, activation='tanh'))
        self.model.add(Dropout(0.2))
        self.model.add(Dense(2, activation='softmax'))
        self.model.summary()
        self.model.compile(loss=keras.losses.categorical_crossentropy,
                      optimizer='adam',
                      metrics=['accuracy'])
        self.model.fit(self.x_test, self.y_test, epochs=10, batch_size=128, verbose=1)   
    
    def prepare_data(self,data_file,mode="rus"):
        
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
            self.x_total.append([(i[4]-i[7])/i[7],(i[5]-i[7])/i[7],(i[7]-i[6])/i[7],i[9]["PVV"],i[9]["PVVREL"],(i[9]["EVWMA9"]-i[9]["EVWMA20"])/i[7]])
        
        self.x_total=numpy.array(self.x_total)
        
        for ind in range(len(self.pa.tickers)): 
            if ind > 5 and ind < len(self.x_total)-6: #and ind < len(x_total)*5/10:
                self.x_test.append(self.x_total[ind-5:ind+1])
                self.x_test[-1]+=self.pa.best_directions[ind-6:ind]#+pa.best_directions[ind+1:ind+3]
                if self.pa.best_directions[ind] > 0:
                    self.y_test.append(self.pa.best_directions[ind])
                elif self.pa.best_directions[ind] < 0:
                    self.y_test.append(0)
                elif self.pa.best_directions[ind] == 0:
                    self.y_test.append(2)
                        
        self.x_test=numpy.array(self.x_test)
        self.x_test = self.x_test.reshape(len(self.x_test), 6*len(self.x_total[0]))
        self.y_test=numpy.array(self.y_test)
        self.x_test = self.x_test.astype('float32')
        self.y_test = keras.utils.to_categorical(self.y_test,num_classes=2)
        self.pa.best_directions=[]

    def get_last_direction(self):
        new_best_directions=[1,1,1,1,1,1]
        
        for ind in range(len(self.pa.tickers)):
            x_check=[]
            if ind >= 6:
                x_check.append(self.x_total[ind-5:ind+1])
                x_check[-1]+=new_best_directions[-6:]
                x_check=numpy.array(x_check)
                x_check = x_check.astype('float32')
                x_check=x_check.reshape(1,6*len(self.x_total[0]))
                predict = self.model.predict(x_check)
                #print predict
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
        print self.pa.analyze_by_day2(self.day_tickers, check_time,start_time,end_time, 0,  delta, stop, take,True,method,ema1,ema2)
        #print new_best_directions
        return new_best_directions
    
    def check_correct_prediction(self):
        prv_best_directions=[1,1,1,1,1,1]
        prev_x_check=[]
        for last_ind in range(len(self.pa.tickers)):
            new_best_directions=[1,1,1,1,1,1]
            x_check=[]
            for ind in range(last_ind):
                #x_check=[]
                if ind >= 6:
                    x_check.append(self.x_total[ind-5:ind+1])
                    x_check[-1]+=new_best_directions[-6:]
                    x_check1=numpy.array(x_check[-1])
                    x_check1 = x_check1.astype('float32')
                    x_check1=x_check1.reshape(1,6*len(self.x_total[0]))
                    predict = self.model.predict(x_check1)
                    #if ind == 125:
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
   
if __name__ == "__main__":
    nnt = NNTrader(model_path = "nn_trade_test_model4.h5",init_model = False)
    try:
        for filename in os.listdir("C:\\Just2Trade Client\\"):
            if filename.find("tickers_") == 0:
                nnt.prepare_data("C:\\Just2Trade Client\\"+filename,"world")
                #nnt.prepare_data("tickers_BTCUSD.txt","world")
                nnt.get_last_direction()
                nnt.check_correct_prediction()
    except Exception as e:
        print e