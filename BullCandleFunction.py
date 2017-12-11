import os
import math
from ib_insync import *
from ibapi.order_condition import PriceCondition
from datetime import datetime, time
from pytz import timezone
import sys

#os.chdir('C:\\Users\\Showvik\\PycharmProjects\\IB Trading 2\\IBTradingInsync')
def myalgo(symbol,clientId,outputfile):
    print(f'Process {os.getpid()} working {symbol}')
    sys.stdout = open(outputfile, "w")
    contract = Stock(symbol,'SMART','USD')
    ib = IB()
    ib.connect('127.0.0.1', 7496, clientId= clientId)
    ib.qualifyContracts(contract)
    print("We are trading " + str(contract.localSymbol))

    #get recent candle info
    bars = ib.reqHistoricalData(
            contract,
            endDateTime='',
            durationStr='2 D',
            barSizeSetting='1 day',
            whatToShow='TRADES',
            useRTH=True,
            formatDate=1)
    high1 = bars[0].high
    print("prior high is " + str(high1))
    low1 = bars[0].low
    print("prior low is " + str(low1))
    open1 = bars[0].open
    print("prior open is " + str(open1))
    close1 = bars[0].close
    print("prior close is " + str(close1))
    if close1 >= open1:
        upperwick1 = high1 - close1
    else:
        upperwick1 = high1 - open1

    if close1 >= open1:
        lowerwick1 = open1 - low1
    else:
        lowerwick1 = close1 - low1

    body1 = close1 - open1
    print("body is " + str(body1))
    fullcandle1 = high1 - low1
    print("full candle in points is " + str(fullcandle1))

    ##(ABS(H-C) + ABS(O-L))*2 > ABS(C-O)
    ##ABS(H-C) > ABS(H-L)*.3
    def checkopen(value):
        if body1 >= 0 and (upperwick1 + lowerwick1)*2 > abs(body1) and  upperwick1 < abs(fullcandle1)*.3:
            if close1 - (fullcandle1*.2) <= value <= high1  :
                return True
            return False
        elif body1 >= 0 and upperwick1 > abs(fullcandle1)*.3:
            if open1 - (fullcandle1*.2) <= value <= close1 + (upperwick1*.35):
                return True
            return False
        elif body1 < 0:
            if close1 <= value <= open1:
                return True
            return False
        else:
            return False


    def entryprice():
        if body1 >= 0 and (upperwick1 + lowerwick1) * 2 > abs(body1) and upperwick1 < abs(fullcandle1) * .3:
            return high1
        elif body1 >= 0 and upperwick1 > abs(fullcandle1) * .3:
            return close1 + (upperwick1*.4)
        elif body1 < 0:
            return open1
        else:
            return float('nan')
    print("today's entry price is" + str(entryprice()))
    risk = fullcandle1 *.5
    print("total risk in points is " + str(risk))
    def stoplossprice():
        return entryprice() - risk

    print("today's initial stop loss price is " + str(stoplossprice()))

    #defining number of shares to trade
    maxloss = 10000
    NumOfShares = int(math.floor((maxloss/2) / risk) / 100) * 100
    print("we are trading total of " + str(NumOfShares)+ " shares" )
    #defining orders
    entryorder = MarketOrder('BUY', NumOfShares *2 ,  algoStrategy='Adaptive',algoParams=[TagValue('adaptivePriority', 'Normal')])

    stoploss1 = MarketOrder('SELL', NumOfShares, algoStrategy='Adaptive', algoParams=[TagValue('adaptivePriority', 'Normal')],
                            conditions = [PriceCondition(0, contract.conId, exch= "SMART", isMore= False, price = stoplossprice())])

    stoploss2 = MarketOrder('SELL', NumOfShares, algoStrategy='Adaptive', algoParams=[TagValue('adaptivePriority', 'Normal')],
                            conditions = [PriceCondition(0, contract.conId, exch= "SMART", isMore= False, price = stoplossprice())])

    def getTrade(order):
        for trade in ib.trades():
            if trade.order is order:
                return trade
            else:
                None

    def cancelifexists(order):
        for trade in ib.trades():
            if trade.order is order:
                ib.cancelOrder(order)
            else:
                None
    def exitprocess():
        if Trade.isActive(getTrade(stoploss1)) or Trade.isActive(getTrade(stoploss2)):
            cancelifexists(stoploss1)
            cancelifexists(stoploss2)
            exitorder = MarketOrder('SELL', Trade.remaining(getTrade(entryorder)), algoStrategy='Adaptive',algoParams=[TagValue('adaptivePriority', 'Normal')])
            ib.placeOrder(contract, exitorder)
        else:
            None
    ##stop loss is prior high - fullcandle*.5

    ##if low of the day is lower or equal to entry price, and checkopen() is True and marketprice >= entryprice than the trade is on

    # #get the tickers and subscribe to market
    ticker = ib.reqTickers(contract)# I get ticker as NoneType if I use ib.ticker
    ib.reqMktData(contract, '', False, False)

    #check if its 3:45 pm
    now = datetime.now(timezone('US/Eastern'))
    now_time = now.time()
    def checktime():
        if now_time >= time(15,45):
            return True
        return False

    def checkopenprint():
        if checkopen(ticker[-1].open):
            if body1 >= 0 and (upperwick1 + lowerwick1) * 2 > abs(body1) and upperwick1 < abs(fullcandle1) * .3:
                print("prior candle not enough retracement and today's open is " + str(
                    ticker[-1].open) + "which is  between " + str(close1 - (fullcandle1 *.2)) + "and " + str(
                    high1 ))
            elif body1 >= 0 and upperwick1 > abs(fullcandle1) * .3:
                print("prior candle a lot of retracement and today's open is " + str(
                    ticker[-1].open) + "which is  between " + str(open1 - (fullcandle1*.2)) + "and " + str(close1 + (upperwick1 * .35)))
            elif body1 < 0:
                print("prior candle is red and today's open is " + str(ticker[-1].open) + "which is between " + str(
                    close1) + "and " + str(open1))
            else:
                print("former candle not defined")
        else:
            if body1 >= 0 and (upperwick1 + lowerwick1) * 2 > abs(body1) and upperwick1 < abs(fullcandle1) * .3:
                print("prior candle not enough retracement and today's open is " + str(
                    ticker[-1].open) + "which is NOT in between " + str(close1 - (fullcandle1 * .2)) + "and " + str(
                    high1 ))
            elif body1 >= 0 and upperwick1 > abs(fullcandle1) * .3:
                print("prior candle a lot of retracement and today's open is " + str(
                    ticker[-1].open) + "which is NOT in between " + str(open1 - (fullcandle1*.2)) + "and " + str(close1 + (upperwick1 * .35)))
            elif body1 < 0:
                print("prior candle is red and today's open is " + str(ticker[-1].open) + "which is NOT in between " + str(
                    close1) + "and " + str(open1))
            else:
                print("former candle not defined")

    print(checkopenprint())
    print("Today's open is " + str(ticker[-1].open) + " and today's low is " + str(ticker[-1].low) )
    print("Today's market price is  " + str(ticker[-1].marketPrice()) + " and today's entry is " + str(entryprice()))
    print("Today's Initial stop loss price is " + str(stoplossprice()))
    # get the open trades and open positions
    while ib.waitOnUpdate():
            if  checkopen(ticker[-1].open) and ticker[-1].low <= entryprice() and ticker[-1].marketPrice() >= entryprice():
                print("trade is on and today's open is " + str(ticker[-1].open) + " and today's low is " + str(ticker[-1].low) )
                print("Current market price is  " + str(ticker[-1].marketPrice()) + " and today's entry is " + str(entryprice()))
                print("Initial stop loss price is " + str(stoplossprice()))
                ib.placeOrder(contract,entryorder)
                ib.placeOrder(contract, stoploss1)
                ib.placeOrder(contract, stoploss2)
                while ib.waitOnUpdate():
                    if ticker[-1].marketPrice() > entryprice() + risk:
                        print("market went up in favor")
                        stoploss1.conditions = [PriceCondition(0, contract.conId, exch= "SMART", isMore= False, price = stoplossprice()+ risk*.5)]
                        print("new stoploss1 price is " + str(stoplossprice()+ risk*.5))
                        ib.placeOrder(contract, stoploss1)
                        while ib.waitOnUpdate():
                            if ticker[-1].marketPrice() > entryprice() + risk*2:
                                print("market went even more in favor")
                                stoploss1.conditions = [PriceCondition(0, contract.conId, exch="SMART", isMore=False, price=stoplossprice() + risk * 1.5)]
                                print("new stoploss1 price is " + str(stoplossprice() + risk * 1.5))
                                ib.placeOrder(contract, stoploss1)
                                stoploss2.conditions = [PriceCondition(0, contract.conId, exch="SMART", isMore=False, price=entryprice())]
                                print("new stoploss2 price is " + str(entryprice()))
                                ib.placeOrder(contract, stoploss2)
                                while ib.waitOnUpdate():
                                    if checktime():
                                        print("market went up as far as it could and now time's up")
                                        exitprocess()
                                        break
                                    else:
                                        print("market went up as far as it could, not waiting for 3.45 pm")
                                        continue
                            elif checktime():
                                print("market did not go further up after initial thrust and TIME's up")
                                exitprocess()
                                break

                            else:
                                continue
                            break
                    elif checktime():
                            print("market did not do anything after initial entry and now time's up")
                            exitprocess()
                            break

                    else:
                        continue
                    break

            elif not checkopen(ticker[-1].open):
                print(checkopenprint())
                break
            elif checktime():
                print("market did not go through entry even though today's open satisfied condition")
            else:
                continue
            break
    print(f'Process {os.getpid()} done processing {symbol}')
    ib.disconnect()







