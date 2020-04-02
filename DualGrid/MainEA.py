from zmq_api import zmq_api
from var_input import var_input

var_input1=var_input()
var_input1.Manual=1
var_input1.Enable=1
var_input1.start_lot=0.1
var_input1.step_lot=0.01
var_input1.symbols=["XAUUSD","AUDCAD","EURUSD","GBPJPY","NZDCHF"]
client1=zmq_api([32780,32781,32782],var_input1)

var_input2=var_input()
var_input2.start_lot=0.05
var_input2.step_lot=0.01
var_input2.symbols=["XAUUSD."]
client2=zmq_api([32790,32791,32792],var_input2)

client1.run()
client2.run()

#client1.ea[0].PrintStatus()