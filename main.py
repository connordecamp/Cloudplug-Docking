import smbus2
from typing import List
import time
from modules.sfp import SFP

class SFP_I2C_Bus:

    # Raspberry Pi uses bus 1 for I2C
    DEVICE_BUS = 1

    # Page 0xA0 of the SFP, stores identifier information
    INFO_ADDR = 0x50

    # Page 0xA2 of the SFP for digital diagnostics monitoring (DDM)
    # Would be 1010 0010, but we ignore the last bit since R/W
    # So we get 101 0001, which is 0x51
    DDM_ADDR = 0x51

    def __init__(self):
        self.bus = smbus2.SMBus(self.DEVICE_BUS)


    def _dump(self, addr: int, max_addr: int) -> List[int]:
        values = []

        try:
            for i in range(max_addr + 1):
                read_value = self.bus.read_byte_data(addr, i)
                values.append(read_value)

        except Exception as ex:
            print("ERROR::SFP_I2C_BUS::_dump()")
            print(ex)
            values = [-1] * max_addr

            raise Exception("Remote I/O error communicating with SFP")

        return values

    def dumpA0(self) -> List[int]:
        return self._dump(self.INFO_ADDR, 0xFF)

    def dumpA2(self) -> List[int]:
        return self._dump(self.DDM_ADDR, 0xFF)


    def end_communication(self):
        self.bus.close()


def print_bus_dump(bus_dump: List[int], ascii: bool) -> None:

    # Print header
    if ascii:
        print(f'0123456789ABCDEF')
    else:
        print('{:>6}{:>3}{:>3}{:>3}{:>3}{:>3}{:>3}{:>3}{:>3}{:>3}{:>3}{:>3}{:>3}{:>3}{:>3}{:>3}'.format('0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F'))

    for idx, num in enumerate(bus_dump):

        if ascii:
            if num >= 32 and num <= 126:
                print(chr(num), end='')
            else:
                print('.', end='')
        else:
            if idx % 16 == 0:
                print(format(idx, '02X') + ':', end=' ')

            print(format(num, '02X'), end=' ')
            

        if (idx + 1) % 16 == 0:
            print()

        


def main():
    
    # Create an SFP_I2C bus object to interact with
    # the SFP connected to the experimenter board
    sfp_bus = SFP_I2C_Bus()

    a0_dump = sfp_bus.dumpA0()
    a2_dump = sfp_bus.dumpA2()

    print("Page 0xA0")
    print_bus_dump(a0_dump, False)
    print_bus_dump(a0_dump, True)
    print("\n\nPage 0xA2")
    print_bus_dump(a2_dump, False)
    print_bus_dump(a2_dump, True)


    # Create an sfp defined in modules/sfp,py
    sfp = SFP(a0_dump, a2_dump)

    # just debug, print diagnostic monitoring type
    print(sfp.get_diagnostic_monitoring_type())

    
    print("{:<20} {:<20} {:<30} {:<30} {:<30}".format("Temperature (C)", "Voltage (V)", "TX Bias Current (mA)", "TX Power (0.1 uW)", "RX Power (0.1 uW)"))
    # print(sfp.get_voltage_slope())
    #print(sfp.get_voltage_offset())
    while True:
        
        try:
            # Format measurements nicely
            print("{:<20.5f} {:<20.5f} {:<30.5f} {:<30.5f} {:<30.5f}".format(sfp.get_temperature(), 
                sfp.get_vcc() * 10**(-4), 
                sfp.get_tx_bias_current() * 2 * 10**(-3), 
                sfp.get_tx_power(), 
                sfp.get_rx_power())
            )

            # re-read the entirety of diagnostics memory
            # should probably create a new function that ONLY
            # reads the few values we need
            a2_dump = sfp_bus.dumpA2()
            
            # Update the page in the sfp object
            sfp.page_a2 = a2_dump

            # Sleep for some time
            time.sleep(0.5)
        except KeyboardInterrupt as ex:
            print("\nKeyboard Interrupt, closing bus communication and exiting...")
            sfp_bus.end_communication()
            return
    
    
if __name__ == '__main__':
    main()