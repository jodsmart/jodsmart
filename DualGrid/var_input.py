class var_input:
   
    def __init__(self):
        self.line_token="QIigVnDkALwcSo5ZnDLDf1VZOvxIzMvDTfo6QBAamDK"
        self.Manual=1
        self.Enable=1
        self.long_only=1
        self.short_only=1
        self.TP=100
        self.SL=100
        self.Trail=50
        self.Order_diff=100
        self.list_cut=3
        self.swap_side=2
        self.Multiply=1.5
        self.candle_trend=4 #min 1
        self.MM=0 #0=disable 1=enable
        self.start_lot=0.10
        self.step_lot=0.01
        self.start_money=100
        self.symbols=["AUDCAD","AUDCHF","AUDJPY","AUDNZD","AUDUSD","CADCHF","CADJPY",
                    "CHFJPY","EURAUD","EURCAD","EURCHF","EURGBP","EURJPY","EURNZD",
                    "EURUSD","GBPAUD","GBPCAD","GBPCHF","GBPJPY","GBPNZD","GBPUSD",
                    "NZDCAD","NZDCHF","NZDJPY","NZDUSD","USDCAD","USDCHF","USDJPY"]
        self.postfix="."
        self.p_range_over=0
        self.p_range_under=0
        # PERIOD M5=5 M30=30 H1=60 H4=240 D1=1440 W1=10080 MN=43200
        self.timeframe=60
        self.i_timeframe=1440
        
        self.atr_period=80
        
        #Method SMA=0 EMA=1 SMMA=2 LWMA=3
        #Applied Price Close=0 Open=1 High=2 Low=3 HL/2=4 HLC/3=5 Weight_HLCC/4=6
        self.fma_period=14
        self.fma_method=1
        self.fma_applied=0
        
        self.sma_period=20
        self.sma_method=0
        self.sma_applied=0
