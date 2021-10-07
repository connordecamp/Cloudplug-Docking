from typing import List
from enum import Enum
import struct
import time
from decimal import Decimal

import mysql.connector

from modules.core.sfp import SFP
from modules.core.sfp_i2c_bus import SFP_I2C_Bus, print_bus_dump

from modules.network.non_qt_udp_client import MyUdpSocket, MyUdpSocketState
from modules.network.non_qt_tcp_client import MySocket, MyTcpSocketState
from modules.network.message import MeasurementMessage, Message, MessageCode, unpackRawBytes
from modules.network.db_utility import *

def test_bus_dump():
    
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
            print("{:<20.5f} {:<20.5f} {:<30.5f} {:<30.5f} {:<20.5f}".format(sfp.get_temperature(), 
                sfp.get_vcc() * Decimal(10**(-4)), 
                sfp.get_tx_bias_current() * Decimal(2 * 10**(-3)), 
                sfp.get_tx_power(), 
                sfp.calculate_rx_power_uw())
            )

            # re-read the entirety of diagnostics memory
            # should probably create a new function that ONLY
            # reads the few values we need
            i = 96
            for register_val in sfp_bus.read_param_registers():
                sfp.page_a2[i] = register_val
                i += 1

            # Sleep for some time
            time.sleep(0.5)
        except KeyboardInterrupt as ex:
            print("\nKeyboard Interrupt, closing bus communication and exiting...")
            sfp_bus.end_communication()
            return
    

def main():

    my_udp_socket = MyUdpSocket()
    my_tcp_socket = MySocket()

    server_ip = None
    server_port = None

    mydb = None
    mycursor = None

    sfp_inserted = False

    sfp_bus = SFP_I2C_Bus()

    while True:
        
        while my_udp_socket.state == MyUdpSocketState.UNDISCOVERED:
            try:
                raw_msg = my_udp_socket.myrecv()
                received_cmd: Message = unpackRawBytes(raw_msg)

                if received_cmd.code == MessageCode.DISCOVER:
                    print('Has been discovered by the server')

                    msg = Message(MessageCode.DOCK_DISCOVER_ACK, 'DOCKING STATION DISCOVERED')
                    print(f'Writing {msg.to_network_message()}')
                    my_udp_socket.sock.sendto(msg.to_network_message(), (my_udp_socket.server_ip, my_udp_socket.server_port))
                    my_udp_socket.state = MyUdpSocketState.DISCOVERED

                    server_ip = my_udp_socket.server_ip
                    server_port = my_udp_socket.server_port

                    # Stop accepting broadcasts from the server once
                    # it has been discovered. We don't want to process
                    # thousands of backlogged discover requests
                    # if we disconnect an hour into the application
                    # running.
                    my_udp_socket.sock.close()       


            except Exception as ex:
                print(ex)

            time.sleep(0.5)
            print('Waiting for message...')
        
        # If we reach this point, the docking station has been discovered
        # Attempt to initiate TCP connection with the server

        try:
            print(f'Attempting to connect to {server_ip}:{server_port}')
            my_tcp_socket.connect(server_ip, server_port)
            print(f'Connection successful!')
        except Exception as ex:
            # If there is an exception while connecting,
            # change the state of the udp socket to
            # undiscovered to allow reconnection
            print(ex)
            print('Connection error, reverting to undiscovered state')
            my_udp_socket = MyUdpSocket()
            my_udp_socket.state = MyUdpSocketState.UNDISCOVERED
            continue

        while my_tcp_socket.state == MyTcpSocketState.CONNECTED:
                        
            #test_data = 'This is a CloudPlug'
            #msg = Message(2411, test_data)
            #my_tcp_socket.mysend(msg.to_network_message())

            print('Awaiting TCP commands...')
            raw_msg = my_tcp_socket.myreceive()
            received_cmd: Message = unpackRawBytes(raw_msg)
            
            print(received_cmd)

            if received_cmd.code == MessageCode.CLONE_SFP_MEMORY:
                print('Trying to read SFP memory!')
                try:
                    a0_dump = sfp_bus.dumpA0()
                    a2_dump = sfp_bus.dumpA2()

                    #print("Page 0xA0")
                    #print_bus_dump(a0_dump, False)
                    #print_bus_dump(a0_dump, True)
                    #print("\n\nPage 0xA2")
                    #print_bus_dump(a2_dump, False)
                    #print_bus_dump(a2_dump, True)
                    
                    try:
                        mydb = mysql.connector.connect(
                            host=server_ip,
                            user="connor",
                            password="cloudplug!@#@!",
                            database="sfp_info",
                            autocommit=True
                        )

                        mycursor = mydb.cursor()         
                        insert_cloned_memory_to_database(mycursor, a0_dump, a2_dump)
                        code = MessageCode.CLONE_SFP_MEMORY_SUCCESS
                        data = "Successfully cloned SFP memory"
                        msg = Message(code, data)

                        my_tcp_socket.mysend(msg.to_network_message())

                    except Exception as ex:
                        print(ex)
                
                except Exception as ex:
                    code = MessageCode.CLONE_SFP_MEMORY_ERROR
                    data = "Error communicating with SFP"
                    msg = Message(code, data)
                    my_tcp_socket.mysend(msg.to_network_message())
                    print(ex)
                finally:
                    sfp_bus.close()
            elif received_cmd.code == MessageCode.REQUEST_SFP_PARAMETERS:
                # we want to read the data and send it back to control software

                try:
                    new_data = sfp_bus.read_param_registers()
                    print(new_data)
                    code = MessageCode.REQUEST_SFP_PARAMETERS_ACK

                    msg = MeasurementMessage(code, new_data)

                    my_tcp_socket.mysend(msg.to_network_message())
                    

                except Exception as ex:
                    print("ERROR")
                    print(ex)



            time.sleep(0.3)

        time.sleep(1)
            


    return

    

if __name__ == '__main__':
    main()