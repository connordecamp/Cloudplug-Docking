from main import insert_sfp_data_to_table
import struct
import time

from modules.network.non_qt_udp_client import MyUdpSocket, MyUdpSocketState
from modules.network.non_qt_tcp_client import MySocket, MyTcpSocketState
from modules.network.message import Message, MessageCode

import mysql.connector

def main():

    my_udp_socket = MyUdpSocket()
    my_tcp_socket = MySocket()

    server_ip = None
    server_port = None

    mydb = None
    mycursor = None

    while True:
        
        while my_udp_socket.state == MyUdpSocketState.UNDISCOVERED:
            try:
                raw_msg = my_udp_socket.myrecv()
                code, data = struct.unpack('!H254s', raw_msg)
                received_cmd = Message(code, str(data, 'utf-8').strip('\x00'))

                if code == MessageCode.DISCOVER.value:
                    print('Has been discovered by the server')

                    msg = Message(MessageCode.CLOUDPLUG_DISCOVER_ACK.value, 'CLOUDPLUG DISCOVERED')
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

                    mydb = mysql.connector.connect(
                        host=server_ip,
                        user="connor",
                        password="cloudplug",
                        database="sfp_info"
                    )

                    mycursor = mydb.cursor()                


            except Exception as ex:
                print(ex)

            time.sleep(1)
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
            print('Awaiting TCP commands...')
            
            
            test_data = 'This is a CloudPlug'
            msg = Message(2411, test_data)

            my_tcp_socket.mysend(msg.to_network_message())
            time.sleep(2)

            msg = None # (pretend this is a command code)

            '''
            if MessageCode(msg) == READ_SFP_MEMORY:
                a0_dump = sfp_bus.dumpA0()
                a2_dump = sfp_bus.dumpA2()

                insert_sfp_data_to_table(mycursor, "sfp", values)
                mydb.commit()
                insert_sfp_data_to_table(mycursor, "page_a0", values)
                mydb.commit()
                insert_sfp_data_to_table(mycursor, "page_a2", values)
            '''

        time.sleep(1)
            


    return

if __name__ == '__main__':
    main()
