from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime
import backtrader as bt
from backtrader.dataseries import TimeFrame
class  PriceMACross(bt.Strategy):
    params = (
        ('smaperiod', 155),
    )
    def log(self, txt, dDay=None, dTime=None):
        """Вывод строки с датой на консоль"""
        dDay = bt.num2date(self.datas[0].datetime[0]).date() if dDay is None else dDay  # Заданная дата или дата текущего бара
        dTime = bt.num2date(self.datas[0].datetime[0]).time() if dTime is None else dTime  # Заданная дата или дата текущего бара
        print(f' {dDay.strftime("%d.%m.%Y")} {dTime.strftime("%H:%M.%S")}, {txt}')  # Выводим дату с заданным текстом на консоль

    def __init__(self):
        """Инициализация торговой системы"""
        self.close = self.datas[0].close  # Цены закрытия
        self.order = None  # Заявка
        self.sma = bt.indicators.MovingAverageSimple(
            self.datas[0], period=self.params.smaperiod)
        self.buyprice = None
        bt.observers.BuySell

    def notify_order(self, order):
        """Изменение статуса заявки"""
        if order.status in [order.Submitted,
                            order.Accepted]:  # Если заявка не исполнена (отправлена брокеру или принята брокером)
            return  # то статус заявки не изменился, выходим, дальше не продолжаем
        if order.status in [order.Completed]:  # Если заявка исполнена
            if order.isbuy():  # Заявка на покупку
                self.log(
                    f'Bought @{order.executed.price:.2f}, Cost={order.executed.value:.2f}, Comm={order.executed.comm:.2f}')
                self.bar_executed = len(self)
                self.buyprice = order.executed.price
            elif order.issell():  # Заявка на продажу
                self.log(
                    f'Sold @{order.executed.price:.2f}, Cost={order.executed.value:.2f}, Comm={order.executed.comm:.2f}')
        elif order.status in [order.Canceled, order.Margin,
                              order.Rejected]:  # Заявка отменена, нет средств, отклонена брокером
            self.log('Canceled/Margin/Rejected')
        self.order = None  # Этой заявки больше нет

    def notify_trade(self, trade):
        """Изменение статуса позиции"""
        if not trade.isclosed:  # Если позиция не закрыта
            return  # то статус позиции не изменился, выходим, дальше не продолжаем

        self.log(f'Trade Profit, Gross={trade.pnl:.2f}, NET={trade.pnlcomm:.2f}')

    def next(self):
        """Получение следующего бара"""
        self.log(f'Close={self.close[0]:.2f}')
        if self.order:  # Если есть неисполненная заявка
            return  # то выходим, дальше не продолжаем

        if not self.position:  # Если позиции нет
            isSignalBuy = self.close[0] > self.sma[0]  # Цена закрылась выше скользящцей
            if isSignalBuy:  # Если пришла заявка на покупку
                self.log('Buy Market')
                self.order = self.buy()  # Заявка на покупку по рыночной цене
        else:  # Если позиция есть
            isSignalSell = self.close[0] < self.sma[0]  # Цена закрылась ниже скользящей
            if isSignalSell:  # Если пришла заявка на продажу
                self.log('Sell Market')
                self.order = self.sell(exectype=bt.Order.Market)  # Заявка на продажу по рыночной цене


if __name__ == '__main__':
    cerebro = bt.Cerebro(stdstats=True, cheat_on_open=True)
    cerebro.addstrategy(PriceMACross)  # Привязываем торговую систему с параметрами
    cerebro.broker.setcash(1000000)
    data = bt.feeds.GenericCSVData(
        dataname='mmu4.csv',
        headers = False,
        timeframe =TimeFrame.Minutes,
        datetime=0,
        time=1,
        open=2,
        high=3,
        low=4,
        close=5,
        volume=6,
        openinterest=-1,
        separator= ';',
        dtformat='%Y%m%d',
        tmformat='%H%M%S',
        fromdate=datetime.datetime(2024, 5, 24),
        todate=datetime.datetime(2024, 5, 25)
    )
    cerebro.adddata(data)
    cerebro.addsizer(bt.sizers.FixedSize, stake=1)  # Кол-во акций для покупки/продажи
    cerebro.broker.setcommission(commission=0.001)  # Комиссия брокера 0.1% от суммы каждой исполненной заявки
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='TradeAnalyzer')  # Привязываем анализатор закрытых сделок
    brokerStartValue = cerebro.broker.getvalue()  # Стартовый капитал
    print(f'Старовый капитал: {brokerStartValue:.2f}')
 #   cerebro.addobserver(bt.observers.BuySell, barplot=True, bardist=0.0025)
    cerebro.addobserver(bt.observers.BuySell, barplot=True, bardist=0.0025)
    cerebro.addobserver(bt.observers.Broker)
    cerebro.addobserver(bt.observers.Trades)
  #  bt.observers.BuySell.params.barplot = True
  #  bt.observers.BuySell.params.bardist=0.0025
    result = cerebro.run(stdstats = False)  # Запуск торговой системы
    brokerFinalValue = cerebro.broker.getvalue()  # Конечный капитал
    print(f'Конечный капитал: {brokerFinalValue:.2f}')
    print(f'Прибыль/убытки с комиссией: {(brokerFinalValue - brokerStartValue):.2f}')
    analysis = result[0].analyzers.TradeAnalyzer.get_analysis()  # Получаем данные анализатора закрытых сделок
    print('Прибыль/убытки по закрытым сделкам:')
    print(f'- Без комиссии {analysis["pnl"]["gross"]["total"]:.2f}')
    print(f'- С комиссией  {analysis["pnl"]["net"]["total"]:.2f}')
    c=bt.observers.BuySell.params
#    print(bt.observers.BuySell.__dict__)
    cerebro.plot()  # Рисуем график

