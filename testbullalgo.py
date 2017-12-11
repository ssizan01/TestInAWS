import os
os.chdir('C:\\Users\\Showvik\\PycharmProjects\\TestingAlgoInPycharm')
from multiprocessing import Pool
import time
import BullCandleFunction
myalgo = BullCandleFunction.myalgo
symbols = ["MRVL", "CAT", "MS","AMT","QCOM","URI","UAL","CSCO","DAL","INTC"]
clientIds = list(range(0,len(symbols)))
outputfiles = []
for i in range(0,len(symbols)):
    outputfiles.append('Log' + str(i)+'.txt')



if __name__ == '__main__':
    start = time.time()
    p = Pool(len(symbols))
    results = p.starmap(myalgo, zip(symbols,clientIds,outputfiles))
    end = time.time()
    print(f'\nTime to complete: {end - start:.2f}s\n')
    p.close()
    p.join()

