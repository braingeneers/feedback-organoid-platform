from tecancavro.models import CentrisB

from tecancavro.transport import TecanAPISerial

# Functions to return instantiated CentrisB objects for testing

def returnSerialCentrisB():
    test0 = CentrisB(com_link=TecanAPISerial(0, '/dev/ttyUSB0', 9600))
    return test0

def findSerialPumps():
    return TecanAPISerial.findSerialPumps()

def getSerialPumps():
    ''' Assumes that the pumps are CentrisB pumps and returns a list of
    (<serial port>, <instantiated CentrisB>) tuples
    '''
    pump_list = findSerialPumps()
    return [(ser_port, CentrisB(com_link=TecanAPISerial(0,
             ser_port, 9600))) for ser_port, _, _ in pump_list]


if __name__ == '__main__':
    print(findSerialPumps())
    print(returnSerialCentrisB())
