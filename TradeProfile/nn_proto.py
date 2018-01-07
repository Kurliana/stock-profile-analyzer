'''
Created on 6 Jan 2018

Test module for Keras neuron network

@author: Kurliana
'''


import numpy
from ProfileAnalyzerTest import ProfileAnalyser
import keras
from keras.preprocessing import sequence
from keras.utils import np_utils
from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten,Activation
from keras.layers import Conv2D, MaxPooling2D,LSTM
from keras import backend as K

num_classes=2

pa = ProfileAnalyser("FEES_150105_170801.txt",mode="rus")

day_tickers = pa.filter_tickers(pa.tickers, pa.begin_time,pa.max_time-1000,-1,-1)
pa.tickers = day_tickers

x_total=[]
y_total=[]
x_train=[]
y_train=[]
x_test=[]
y_test=[]

def convert_to_comp_array(ticker):
    comp_array=[]
    if abs(ticker[4]-ticker[7]) > 0:
        comp_array.append(ticker[4]-ticker[7]/abs(ticker[4]-ticker[7]))
    else:
        comp_array.append(0)
    if abs(ticker[5]-ticker[7]) > 0:
        comp_array.append(ticker[5]-ticker[7]/abs(ticker[5]-ticker[7]))
    else:
        comp_array.append(0)
    if abs(ticker[7]-ticker[6]) > 0:
        comp_array.append(ticker[7]-ticker[6]/abs(ticker[7]-ticker[6]))
    else:
        comp_array.append(0)
    if abs(ticker[9]["PVVREL"]) > 0:
        comp_array.append(ticker[9]["PVVREL"]/abs(ticker[9]["PVVREL"]))
    else:
        comp_array.append(0)
    if abs(ticker[9]["PVV"]) > 0:
        comp_array.append(ticker[9]["PVV"]/abs(ticker[9]["PVV"]))
    else:
        comp_array.append(0)
    if abs(ticker[9]["EVWMA9"]-ticker[9]["EVWMA20"]) > 0:
        comp_array.append(ticker[9]["EVWMA9"]-ticker[9]["EVWMA20"]/abs(ticker[9]["EVWMA9"]-ticker[9]["EVWMA20"]))
    else:
        comp_array.append(0)
    return comp_array

wrong = 0
for ind in range(len(pa.tickers)):
    i = pa.tickers[ind]

    x_total.append([(i[4]-i[7])/i[7],(i[5]-i[7])/i[7],(i[7]-i[6])/i[7],i[9]["PVV"],i[9]["PVVREL"],(i[9]["EVWMA9"]-i[9]["EVWMA20"])/i[7]])
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
    
print y_total[:10]

x_total=numpy.array(x_total)
for ind in range(len(pa.tickers)): 
    if ind > 6 and ind <= len(x_total)*7/10:
        x_train.append(x_total[ind-5:ind+1])
        print "BEFORE"
        print x_train[-1]
        x_train[-1]+=pa.best_directions[ind-5:ind]+[0]#+pa.best_directions[ind+1:ind+3]
        print "AFTER"
        print x_train[-1]
        #x_train[-1][-5][-2] = 0
        #x_train.append(x_total[ind])
        if not pa.best_directions[ind] == 0:
            y_train.append(y_total[ind])
        else:
            del x_train[-1]

    elif ind > len(x_total)*7/10 and ind < len(x_total)-6: #and ind < len(x_total)*5/10:
        x_test.append(x_total[ind-5:ind+1])
        x_test[-1]+=pa.best_directions[ind-5:ind]+[0]#+pa.best_directions[ind+1:ind+3]
        #x_test[-1][-5][-2] = 0
        if not pa.best_directions[ind] == 0:
            y_test.append(y_total[ind])
        else:
            del x_test[-1]
        
        
print y_train[:10]

x_train=numpy.array(x_train)
print(x_train.shape, 'train shape')
x_train = x_train.reshape(len(x_train), 6*len(x_total[0]))
print(x_train.shape, 'train shape')
y_train=numpy.array(y_train)
x_test=numpy.array(x_test)
x_test = x_test.reshape(len(x_test), 6*len(x_total[0]))
y_test=numpy.array(y_test)
x_train = x_train.astype('float32')
x_test = x_test.astype('float32')
y_train = keras.utils.to_categorical(y_train,num_classes=num_classes)
y_test = keras.utils.to_categorical(y_test,num_classes=num_classes)
print y_train[0:10]
#y_train=numpy.expand_dims(y_train, axis=0)
#y_test=numpy.expand_dims(y_test, axis=0)

model = Sequential()
model.add(Dense(51, activation='tanh', input_shape=(6*len(x_total[0]),)))
model.add(Dropout(0.2))
model.add(Dense(51, activation='tanh'))
model.add(Dropout(0.2))
model.add(Dense(num_classes, activation='softmax'))
model.summary()
model.compile(loss=keras.losses.categorical_crossentropy,
              optimizer='adam',
              metrics=['accuracy'])
model.fit(x_train, y_train, epochs=1, batch_size=128, verbose=1,validation_data=(x_test, y_test))
score = model.evaluate(x_test, y_test)
print('Test loss:', score[0])
print('Test accuracy:', score[1])

new_best_directions=[-1,1,1,1,1,1]

x_check=[]

for ind in range(len(pa.tickers)):
    i = pa.tickers[ind]
    x_check.append(x_total[ind+5:ind+1])
    x_check[-1]+=new_best_directions[-6:-1]+[0]
    #x_total.append(i[:-1])
    #for param_name in i[9].keys():
    #    x_total[-1].append(i[9][param_name])
    if ind >= 6:
        predict = model.predict(numpy.expand_dims(x_check[-1].reshape(1,6*len(x_total[0])), axis=0))
        if predict[0][0] > predict[0][1]:
            new_best_directions.append(-1)
        else:
            new_best_directions.append(1)
            
if not len(x_total) == len(new_best_directions):
    print "ERROR: tickers %s and directions %s" % (len(x_total),len(new_best_directions))
    exit(0)


day_tickers = pa.filter_tickers(pa.tickers, pa.begin_time,pa.max_time-1000,-1,-1)
pa.tickers = day_tickers
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