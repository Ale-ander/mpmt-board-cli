import sys
import mmap
import pymodbus.client as ModbusClient
import time
from pymodbus import FramerType, ModbusException

try:
    fid = open('/dev/uio0', 'r+b', 0)
except FileNotFoundError:
    perror("UIO device not found")
    sys.exit(-1)

regs = mmap.mmap(fid.fileno(), 0x10000)

def write(add: int, value: int) -> None:
    global regs
    regs[add*4:(add*4)+4] = int.to_bytes(value, 4, byteorder='little')


def read(add: int) -> int:
    global regs
    return int.from_bytes(regs[add*4:(add*4)+4], byteorder='little')

if __name__ == '__main__':
    FEB = ModbusClient.ModbusTcpClient('localhost', port=502, framer=FramerType.SOCKET)

    if not FEB.connect():
        print(f'E: host not reachable or mbusd not running ({self.param.host})')
        sys.exit(1)

    for i in range(1, 20):
        write(1, 2**(i-1))
        print(f'Turned on socket {i}')
        time.sleep(1)
        rr = FEB.write_register(address=0, value=i, slave=20)
        if rr.isError():
            print('Board not connected')
        else:
            print(f'Address changed')
            
        time.sleep(1)
        write(1, 0)
