from typing import List
import time
from enum import Enum

import mysql.connector

from modules.sfp import SFP
from modules.sfp_i2c_bus import SFP_I2C_Bus, print_bus_dump

class TableNames(Enum):
    ID = 0
    PAGE_A0 = 1
    PAGE_A2 = 2

def _get_number_of_columns_in_table(cursor, table_name: str) -> int:
    sql_statement = f"select count(*) as count from information_schema.columns where table_name\'{table_name}\'"
    cursor.execute(sql_statement)
    result = cursor.fetchone()

    columns_in_table = result[0] - 1

    return columns_in_table

def insert_sfp_data_to_table(cursor, table_id: TableNames, values: List[int]) -> None:

    def insert_to_id_table():
        table_name = "sfp"
        # gets number of columns in database
        
        columns_in_table = _get_number_of_columns_in_table(cursor, table_name)

        if len(values) != columns_in_table:
            raise Exception("")

        sql_statement = f"INSERT INTO {table_name} (vendor_id, vendor_part_number, transceiver_type) VALUES (%s, %s, %s)"
        vals_to_insert = tuple(values)
        cursor.execute(sql_statement, vals_to_insert)

    def insert_to_a0_table():
        table_name = "page_a0"

        sql_statement = f'INSERT INTO {table_name} ('
        for i in range(255):
            sql_statement += f"`{i}`, "
        sql_statement += '`255`) VALUES ('
        for i in range(255):
            sql_statement += "%s, "
        sql_statement += "%s)"

        cursor.execute()
        

    def insert_to_a2_table():
        pass

    

    if table_id is TableNames.ID:
        insert_to_id_table()
    elif table_id is TableNames.PAGE_A0:
        insert_to_a0_table()
    elif table_id is TableNames.PAGE_A2:
        insert_to_a2_table()
    else:
        raise Exception("Unknown tablename")

def main_for_pi():
    
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
    

def main():

    my_udp_socket = MyUdpSocket()
    my_tcp_socket = MySocket()

    server_ip = None
    server_port = None

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

        time.sleep(1)
            


    return

    

if __name__ == '__main__':
    main()