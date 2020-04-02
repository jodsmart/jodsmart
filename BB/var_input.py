class var_input:
  
    def __init__(self):
        self.line_token="yNigOUri5stLMrG1v2J8c8x3r6Wx8f9ZIZbyYK1W08K"
        self.Manual=1  #0=manual 1=auto
        self.Enable=1
        self.long_only=1
        self.short_only=1
        self.TP=100
        self.SL=150
        self.Trail=30
        self.Order_diff=50
        self.Max_order=2
        self.Order_loop=4
        self.candle_trend=4 #min 1
        self.MM=0 #0=disable 1=enable
        self.AutoCalTP=1 #0=disable 1=enable
        self.start_lot=0.01
        self.Multiply=2
        self.start_money=100
        self.symbols=["AUDCAD","AUDCHF","AUDJPY","AUDNZD","AUDUSD","CADCHF","CADJPY",
                    "CHFJPY","EURAUD","EURCAD","EURCHF","EURGBP","EURJPY","EURNZD",
                    "EURUSD","GBPAUD","GBPCAD","GBPCHF","GBPJPY","GBPNZD","GBPUSD",
                    "NZDCAD","NZDCHF","NZDJPY","NZDUSD","USDCAD","USDCHF","USDJPY"]
        self.postfix="."
        # PERIOD M5=5 M30=30 H1=60 H4=240 D1=1440 W1=10080 MN=43200
        self.TimeFrame=60
        
        self.atr_period=26
        
        self.sma_period=20
        self.sma_method=0
        #Applied Price Close=0 Open=1 High=2 Low=3 HL/2=4 HLC/3=5 Weight_HLCC/4=6
        self.sma_applied=0
        
        self.fma_period=14
        #Method SMA=0 EMA=1 SMMA=2 LWMA=3
        self.fma_method=1
        #Applied Price Close=0 Open=1 High=2 Low=3 HL/2=4 HLC/3=5 Weight_HLCC/4=6
        self.fma_applied=0
