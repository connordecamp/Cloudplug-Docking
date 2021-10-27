from typing import List
import struct
import time
import logging

import mysql.connector

from modules.core.sfp_i2c_bus import SFP_I2C_Bus

from modules.network.non_qt_udp_client import UDPSocket, UDPSocketState
from modules.network.non_qt_tcp_client import TCPSocket, TCPSocketState
from modules.network.message import Message, MessageCode, ReadRegisterMessage, bytesToReadRegisterMessage, unpackMeasurementMessageBytes, unpackRawBytes
from modules.network.db_utility import *
    


def main():

    my_udp_socket = None
    my_tcp_socket = None

    server_ip = None
    server_port = None

    mydb = None
    mycursor = None

    sfp_bus = SFP_I2C_Bus()

    log_fmt = "[%(asctime)s | %(levelname)s]: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=log_fmt, datefmt="%I:%M:%S")
    logging.debug("Application started")

    while True:

        if not my_udp_socket:
            logging.debug("Creating UDP Socket")
            my_udp_socket = UDPSocket()

        
        while my_udp_socket.state == UDPSocketState.UNDISCOVERED:
            try:
                raw_msg = my_udp_socket.myrecv()
                received_cmd: Message = unpackRawBytes(raw_msg)

                if received_cmd.code == MessageCode.DISCOVER:
                    logging.debug('Has been discovered by the server')

                    msg = Message(MessageCode.DOCK_DISCOVER_ACK, 'DOCKING STATION DISCOVERED')
                    #logging.debug(f'Writing {msg.to_network_message()}')
                    my_udp_socket.sock.sendto(msg.to_network_message(), (my_udp_socket.server_ip, my_udp_socket.server_port))
                    my_udp_socket.state = UDPSocketState.DISCOVERED

                    server_ip = my_udp_socket.server_ip
                    server_port = my_udp_socket.server_port

                    # Stop accepting broadcasts from the server once
                    # it has been discovered. We don't want to process
                    # thousands of backlogged discover requests
                    # if we disconnect an hour into the application
                    # running.
                    my_udp_socket.sock.close()


            except Exception as ex:
                logging.debug(ex)

            time.sleep(1)
            logging.debug('Waiting for message...')
        
        # If we reach this point, the docking station has been discovered
        # Attempt to initiate TCP connection with the server

        if not my_tcp_socket:
            logging.debug("Creating TCP socket")
            my_tcp_socket = TCPSocket()

        try:
            logging.debug(f'Attempting to connect to {server_ip}:{server_port}')
            my_tcp_socket.connect(server_ip, server_port)
            logging.debug(f'Connection successful!')
            my_udp_socket = None
        except Exception as ex:
            # If there is an exception while connecting,
            # change the state of the udp socket to
            # undiscovered to allow reconnection
            logging.debug(ex)
            logging.debug('Connection error, reverting to undiscovered state')
            my_udp_socket = None
            break

        while my_tcp_socket.state == TCPSocketState.CONNECTED:
                        
            #test_data = 'This is a CloudPlug'
            #msg = Message(2411, test_data)
            #my_tcp_socket.mysend(msg.to_network_message())

            logging.debug('Awaiting TCP commands...')
            try:
                raw_msg = my_tcp_socket.myreceive()
            except RuntimeError as ex:
                my_tcp_socket.handle_server_disconnect()
                my_tcp_socket = None
                break

            msg_code_int, *garbage = struct.unpack("!H254x", raw_msg)
            code = MessageCode(msg_code_int)

            register_read_cmds = [MessageCode.REAL_TIME_REFRESH, MessageCode.DIAGNOSTIC_INIT_A0, MessageCode.DIAGNOSTIC_INIT_A2]

            if code in register_read_cmds:
                received_cmd: ReadRegisterMessage = bytesToReadRegisterMessage(raw_msg)
            else:
                received_cmd: Message = unpackRawBytes(raw_msg)

            if received_cmd.code == MessageCode.CLONE_SFP_MEMORY:
                logging.debug('Trying to read SFP memory!')
                try:
                    a0_dump = sfp_bus.dumpA0()
                    a2_dump = sfp_bus.dumpA2()

                    #logging.debug("Page 0xA0")
                    #print_bus_dump(a0_dump, False)
                    #print_bus_dump(a0_dump, True)
                    #logging.debug("\n\nPage 0xA2")
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
                        logging.debug(ex)
                
                except Exception as ex:
                    code = MessageCode.CLONE_SFP_MEMORY_ERROR
                    data = "Error communicating with SFP"
                    msg = Message(code, data)
                    my_tcp_socket.mysend(msg.to_network_message())
                    logging.debug(ex)
            elif received_cmd.code in register_read_cmds:

                response_vals = []
                try:
                    
                    response_vals = sfp_bus.read_registers_from_page(received_cmd.register_numbers, received_cmd.page_number)

                    if received_cmd.code == MessageCode.REAL_TIME_REFRESH:
                        msg_code = MessageCode.REAL_TIME_REFRESH_ACK
                    elif received_cmd.code == MessageCode.DIAGNOSTIC_INIT_A0:
                        msg_code = MessageCode.DIAGNOSTIC_INIT_A0_ACK
                    elif received_cmd.code == MessageCode.DIAGNOSTIC_INIT_A2:
                        msg_code = MessageCode.DIAGNOSTIC_INIT_A2_ACK

                    msg_response = ReadRegisterMessage(msg_code, "", received_cmd.page_number, response_vals)
                    my_tcp_socket.mysend(msg_response.to_network_message())
                    
                except Exception as ex:
                        # Send I2C error code
                    msg = Message(MessageCode.I2C_ERROR, "Remote I/O error when reading SFP")
                    my_tcp_socket.mysend(msg.to_network_message())


            time.sleep(0.3)

        time.sleep(1)
            


    return

    

if __name__ == '__main__':
    main()