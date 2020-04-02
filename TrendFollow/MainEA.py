from zmq_api import zmq_api
from var_input import var_input

# var_input1=var_input()
# var_input1.Enable=1
# var_input1.start_lot=0.1
# var_input1.step_lot=0.01
# var_input1.symbols=["XAUUSD","AUDCAD","EURUSD","GBPJPY","NZDCHF"]
# client1=zmq_api([32780,32781,32782],var_input1)
# client1.run()

var_input2=var_input()
var_input2.Enable=1
var_input2.start_lot=0.01
var_input2.step_lot=0.01
var_input2.symbols=["EURUSD"]
var_input2.postfix="."
client2=zmq_api([32790,32791,32792],var_input2)


client2.run()

#client1.ea[0].PrintStatus()