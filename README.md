# Gas Cylinder Filling Safety System — Digital Prototype

First functional simulation of the control and safety logic.

Implemented:
- startup and self-check
- READY / FILLING / WARNING / EMERGENCY / LOCK
- 120 bar warning
- 125 bar emergency shutdown
- sensor fault
- emergency stop
- power failure
- valve command and feedback model
- reset without automatic restart
- event logging

This is a logic simulation only. It is not connected to, and must not directly control, real gas equipment.

Run:
`python prototype.py`

Tests:
`python -m unittest test_prototype.py -v`
