#!/usr/bin/env python
from __future__ import print_function
from __future__ import print_function
import struct
import zmq
import time
from common.numpy_fast import clip
from copy import copy
from selfdrive.services import service_list
from cereal import car
import selfdrive.messaging as messaging
from selfdrive.car.car_helpers import get_car


def steer_thread():
  context = zmq.Context()
  sendcan = messaging.pub_sock(context, service_list['sendcan'].port)
  logcan = messaging.sub_sock(context, service_list['can'].port)

  carstate = messaging.pub_sock(context, service_list['carState'].port)
  carcontrol = messaging.pub_sock(context, service_list['carControl'].port)
  
  CI, CP = get_car(logcan, sendcan, None)

  print("got car", CP.carName)
  CC = car.CarControl.new_message()

  i = 0
  rate = 0.001
  direction = 1

  while True:
    
    # send

    CS = CI.update(CC)

    actuators = car.CarControl.Actuators.new_message()

    if i > 0.9 and direction == 1:
      direction = -1
    if i < -0.9 and direction == -1:
      direction = 1

    i += rate * direction

    axis_3 = clip(i * 1.05, -1., 1.)          # -1 to 1
    actuators.steer = axis_3
    actuators.steerAngle = axis_3 * 43.   # deg

    print("steer", actuators.steer)

    CC.actuators.steer = actuators.steer
    CC.actuators.steerAngle = actuators.steerAngle
    CC.enabled = True
    CI.apply(CC)

    # broadcast carState
    cs_send = messaging.new_message()
    cs_send.init('carState')
    cs_send.carState = copy(CS)
    carstate.send(cs_send.to_bytes())
  
    # broadcast carControl
    cc_send = messaging.new_message()
    cc_send.init('carControl')
    cc_send.carControl = copy(CC)
    carcontrol.send(cc_send.to_bytes())

    # Limit to 100 frames per second
    time.sleep(0.01)


if __name__ == "__main__":
  steer_thread()
