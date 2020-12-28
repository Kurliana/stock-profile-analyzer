'''
Created on 6 Jan 2018

Test module for Keras neuron network

@author: Kurliana
'''


import numpy
import random
from ProfileAnalyzerTest import ProfileAnalyser
import keras
import logging.config
from keras import regularizers
from keras.models import Sequential
from keras.layers import Dense, Dropout,BatchNormalization,LeakyReLU,Activation
from keras.optimizers import SGD, adam
from keras.callbacks import ReduceLROnPlateau
from copy import deepcopy
#logging.config.fileConfig('log.conf')
log=logging.getLogger('main')

num_classes=2
predict_size=6

pa = ProfileAnalyser("RSTI_150105_170801.txt",mode="rus")

day_tickers = pa.filter_tickers(pa.tickers, pa.begin_time,pa.max_time-1000,-1,-1)
pa.tickers = day_tickers
best_directions=numpy.array(pa.best_directions)
x_total=[]
y_total=[]
x_train=[]
y_train=[]
x_test=[]
y_test=[]

def _normalize_parameter(param, delta=0.0000000001):
    return float(int(param/delta))*delta

def convert_to_comp_array(ticker,direction, all_tickers):
    comp_array=[]
    comp_array.append(_normalize_parameter((ticker[7]-ticker[4])/ticker[7]))
    comp_array.append(ticker[9]["OBV"]-all_tickers[0][9]["OBV"])
    #comp_array.append(_normalize_parameter((ticker[5]+ticker[6]-2*ticker[7])/ticker[7]))
    #comp_array.append(_normalize_parameter((ticker[6]-ticker[4])/ticker[7]))
    #comp_array.append(_normalize_parameter((ticker[9]["VWMA9"]-ticker[9]["VWMA20"])/ticker[7]))
    #comp_array.append(_normalize_parameter((ticker[9]["VWMA9"]-ticker[7])/ticker[7]))
    #comp_array.append(_normalize_parameter((ticker[9]["EVWMA9"]-ticker[9]["EVWMA20"])/ticker[7]))
    #comp_array.append((ticker[9]["MININD"]-ticker[9]["MAXIND"])/ticker[7])
    #comp_array.append((ticker[9]["MININD"])/ticker[7]-pa.comission/pa.go)
    #comp_array.append((ticker[9]["MAXIND"])/ticker[7]-pa.comission/pa.go)
    #comp_array.append(_normalize_parameter((ticker[9]["ATR"])/ticker[7]))
    comp_array.append(_normalize_parameter((ticker[7]-all_tickers[0][4])/ticker[7]))
    """for i in range(predict_size-len(all_tickers)):
        comp_array.append(0)
        comp_array.append(0)
        comp_array.append(0)
        comp_array.append(0)
    for all_tickers_id in range(len(all_tickers)-1):
        comp_array.append(_normalize_parameter((all_tickers[all_tickers_id][4]-ticker[7])/ticker[7]))
        comp_array.append(_normalize_parameter((all_tickers[all_tickers_id][5]-ticker[7])/ticker[7]))
        comp_array.append(_normalize_parameter((all_tickers[all_tickers_id][6]-ticker[7])/ticker[7]))
        comp_array.append(_normalize_parameter((all_tickers[all_tickers_id][7]-ticker[7])/ticker[7]))
    """
    """
    if numpy.isnan(direction):
        #print "n %s"%direction
        comp_array.append(1.0)
    else:
        #print "n %s"%direction
        rnd = random.uniform(0,1)
        if not abs(direction) == predict_size:
            comp_array.append(direction*rnd/predict_size)
        else:
            if rnd < 0.7:
                comp_array.append(direction/predict_size)
            else:
                comp_array.append(-direction/predict_size)
            
            elif rnd >= 0.7 and rnd < 0.9:
                if direction >=0:
                    comp_array.append((direction-2)/predict_size)
                else:
                    comp_array.append((direction+2)/predict_size)
            else:
                if direction >=0:
                    comp_array.append((direction-4)/predict_size)
                else:
                    comp_array.append((direction+4)/predict_size)
            """

    return comp_array

for ind in range(len(pa.tickers)):
    i = pa.tickers[ind]

    x_total.append(convert_to_comp_array(i,numpy.sum(best_directions[ind-predict_size:ind]),pa.tickers[max(ind-predict_size+1,0):ind+1]))
    #print numpy.mean(best_directions[ind-predict_size:ind])

    #x_total.append(convert_to_comp_array(i))
    #x_total.append([abs(i[4]-i[7])/i[7],abs(i[5]-i[7])/i[7],abs(i[7]-i[6])/i[7]])
    #for param_name in i[9].keys():
    #    x_total[-1].append(i[9][param_name])
    if pa.best_directions[ind] > 0:
        y_total.append(pa.best_directions[ind])
    elif pa.best_directions[ind] < 0:
        y_total.append(0)
    elif pa.best_directions[ind] == 0:
        y_total.append(2)

#log.info(x_total[-2:])
x_total=numpy.array(x_total)#,dtype=object)
#log.info(x_total[-2:])

for ind in range(len(pa.tickers)): 
    if ind > predict_size-1 and ind <= len(x_total)*7/10:
        if pa.tickers[ind-predict_size][2] <= pa.tickers[ind][2]: 
            x_train.append(deepcopy(x_total[ind-predict_size:ind]))
            #x_train[-1][-1][-1]=(pa.tickers[ind-predict_size][4]-pa.tickers[ind][7])/pa.tickers[ind][7]
            #log.info(x_total[ind-predict_size:ind])
            #x_train[-1].append()
            y_train.append(y_total[ind])
            #x_train[-1]+=pa.best_directions[ind-6:ind]#+pa.best_directions[ind+1:ind+3]
            #print "AFTER"
            #print x_train[-1]
            #x_train[-1][-5][-2] = 0
            #x_train.append(x_total[ind])


    elif ind > len(x_total)*7/10 and ind < len(x_total): #and ind < len(x_total)*5/10:
        if pa.tickers[ind-predict_size][2] <= pa.tickers[ind][2]:
            x_test.append(deepcopy(x_total[ind-predict_size:ind]))
            #x_test[-1][-1][-1]=(pa.tickers[ind-predict_size][4]-pa.tickers[ind][7])/pa.tickers[ind][7]
            y_test.append(y_total[ind])
            #x_test[-1]+=pa.best_directions[ind-6:ind]#+pa.best_directions[ind+1:ind+3]
            #x_test[-1][-5][-2] = 0

x_train=numpy.array(x_train)
x_test=numpy.array(x_test)
x_train = x_train.reshape(len(x_train),len(x_total[0])*predict_size)
x_test = x_test.reshape(len(x_test),len(x_total[0])*predict_size)
y_train=numpy.array(y_train)
y_test=numpy.array(y_test)

#x_train = x_train.astype('float32')
#x_test = x_test.astype('float32')
y_train = keras.utils.to_categorical(y_train,num_classes=num_classes)
y_test = keras.utils.to_categorical(y_test,num_classes=num_classes)

#y_train=numpy.expand_dims(y_train, axis=0)
#y_test=numpy.expand_dims(y_test, axis=0)
"""
model = Sequential()
model.add(Dense(51, activation = "tanh",input_shape=(len(x_total[0])*predict_size,)))
model.add(Dropout(0.2))
model.add(Dense(51, activation = "tanh"))
model.add(Dropout(0.2))
model.add(Dense(num_classes, activation='softmax'))
model.summary()
model.compile(loss=keras.losses.categorical_crossentropy,
              optimizer='adam',
              metrics=['accuracy'])



model.fit(x_train, y_train, epochs=10, batch_size=128, verbose=1,validation_data=(x_test, y_test))
"""
reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.9, patience=5, min_lr=0.000001, verbose=1)
model = Sequential()
model.add(Dense(51, input_shape=(predict_size*len(x_total[0]),)))
model.add(BatchNormalization())
model.add(Activation("tanh"))
model.add(Dropout(0.2))
model.add(Dense(51))
model.add(BatchNormalization())
model.add(Activation("tanh"))
model.add(Dense(2, activation='softmax'))
model.summary()
model.compile(loss=keras.losses.categorical_crossentropy,
              optimizer='adam',
              metrics=['accuracy'])
model.fit(x_train, y_train, epochs=100, batch_size=128, verbose=1, validation_data=(x_test, y_test), callbacks=[])   
score = model.evaluate(x_test, y_test)
print('Test loss:', score[0])
print('Test accuracy:', score[1])

model.save('nn_trade_test_model3.h5')
print "Model saved"

pa = ProfileAnalyser("RSTI_150105_170801.txt",mode="rus")
day_tickers = pa.filter_tickers(pa.tickers, pa.begin_time,pa.max_time-1000,-1,-1)
pa.tickers = day_tickers

best_directions=numpy.array(pa.best_directions)
new_best_directions=[-1,1,1,1,1,1]


x_total=[]
y_total=[]
x_train=[]
y_train=[]
x_test=[]
y_test=[]

wrong = 0
for ind in range(len(pa.tickers)):
    i = pa.tickers[ind]

    x_total.append(convert_to_comp_array(i,numpy.sum(best_directions[ind-predict_size:ind]),pa.tickers[max(ind-predict_size+1,0):ind+1]))
    #x_total.append(convert_to_comp_array(i))
    #x_total.append([abs(i[4]-i[7])/i[7],abs(i[5]-i[7])/i[7],abs(i[7]-i[6])/i[7]])
    #for param_name in i[9].keys():
    #    x_total[-1].append(i[9][param_name])
    if pa.best_directions[ind] >0:
        y_total.append(pa.best_directions[ind])
    elif pa.best_directions[ind] < 0:
        y_total.append(0)
    elif pa.best_directions[ind] == 0:
        y_total.append(2)

x_total=numpy.array(x_total)#,dtype=object)

for ind in range(len(pa.tickers)): 
    if ind > predict_size-1 and ind < len(x_total): #and ind < len(x_total)*5/10:
        if pa.tickers[ind-predict_size][2] <= pa.tickers[ind][2]:
            x_test.append(deepcopy(x_total[ind-predict_size:ind]))
            #x_test[-1][-1][-1]=(pa.tickers[ind-predict_size][4]-pa.tickers[ind][7])/pa.tickers[ind][7]
            #x_test[-1][-5][-2] = 0
            #if not pa.best_directions[ind] == 0:
            y_test.append(y_total[ind])
            #else:
            #    del x_test[-1]
       
x_test=numpy.array(x_test)
x_test = x_test.reshape(len(x_test), predict_size*len(x_total[0]))
y_test=numpy.array(y_test)
#x_test = x_test.astype('float32')
y_test = keras.utils.to_categorical(y_test,num_classes=num_classes)
score = model.evaluate(x_test, y_test)
print('Test loss:', score[0])
print('Test accuracy:', score[1])

for ind in range(len(pa.tickers)):
    best_directions=numpy.array(new_best_directions)
    i = pa.tickers[ind]
    x_check=[]
    if ind >= predict_size and ind < len(x_total):
        if pa.tickers[ind-predict_size][2] <= pa.tickers[ind][2]:
            x_check.append(deepcopy(x_total[ind-predict_size:ind]))
            #x_check[-1][-1][-1]=(pa.tickers[ind-predict_size][4]-pa.tickers[ind][7])/pa.tickers[ind][7]
            #for j in range(1,predict_size+1,1):
            #    x_check[-1][-j][-1]=numpy.sum(best_directions[ind-j-predict_size:ind-j])/predict_size
            x_check=numpy.array(x_check)
            #x_check = x_check.astype('float32')
            x_check=x_check.reshape(1,predict_size*len(x_total[0]))
            predict = model.predict(x_check)
            limit=0.5
            if num_classes == 2:
                if predict[0][0] > limit:
                    new_best_directions.append(-1)
                    log.info(i[:-1]+[x_check[-1][-4:-2],pa.best_directions[ind],-1])
                    #if y_test[ind-6] == 1 and predict[0][0] > 0.75:
                    #    print "Wrong predict down %s" % i
                elif predict[0][1] >= limit:
                    new_best_directions.append(1)
                    log.info(i[:-1]+[x_check[-1][-4:-2],pa.best_directions[ind],1])
                    #if y_test[ind-6] == 0 and predict[0][1] > 0.75:
                    #    print "Wrong predict up %s" % i
                else:
                    new_best_directions.append(0)
            else:
                if max(predict[0][0],predict[0][1],predict[0][2]) == predict[0][0]:
                    new_best_directions.append(-1)
                    log.info(i[:-1]+[x_check[-1],pa.best_directions[ind],-1])
                elif max(predict[0][0],predict[0][1],predict[0][2]) == predict[0][1]:
                    new_best_directions.append(1)
                    log.info(i[:-1]+[x_check[-1],pa.best_directions[ind],1])
                elif max(predict[0][0],predict[0][1],predict[0][2]) == predict[0][2]:
                    new_best_directions.append(0)            
                    log.info(i[:-1]+[pa.best_directions[ind],0])
        else:
            new_best_directions.append(0)   
if not len(x_total) == len(new_best_directions):
    print "ERROR: tickers %s and directions %s" % (len(x_total),len(new_best_directions))
    exit(0)

pa.best_directions=new_best_directions

day_ranges={0:[100000, 104000, 100000, 180000, 1, 0, 0.04, 1, 'simple_0.04', 9, 20],
            1:[100000, 115000, 125000, 170000, 1, 0, 0.04, 1, 'take_innsta_0.01', 9, 20],
            2:[100000, 102000, 134000, 174000, -1, 0, 0.04, 1, 'take_innsta_0.03', 9, 20],
            3:[100000, 112000, 121000, 175000, 1, 0, 0.04, 1, 'take_innsta_0.03', 9, 0],
            4:[100000, 102000, 104000, 172000, 1, 0, 0.04, 0, 'take_innsta_0.015', 14, 27],
            5:[183000, 183000, 183000, 183000,1],
            6:[183000, 183000, 183000, 183000,1]}
begin_time,check_time,start_time,end_time,trade,delta,stop,take,method,ema1,ema2 = day_ranges[0][:11]
print pa.analyze_by_day2(day_tickers, check_time,start_time,end_time, 0,  delta, stop, take,True,method,ema1,ema2)