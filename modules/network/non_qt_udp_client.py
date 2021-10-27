import socket
import time
from enum import Enum
from ipaddress import IPv4Address, IPv4Network, ip_address
from modules.network.message import Message, MessageCode
import struct

def determine_subnet_mask(ip: IPv4Address):
    class_A = IPv4Network("10.0.0.0/8")
    class_B = IPv4Network("172.16.0.0/16")
    class_C = IPv4Network("192.168.1.0/24")


    if ip in class_A:
        return 'class A'

    if ip in class_B:
        return 'class B'

    if ip in class_C:
        return 'class C'


    return 'Unknown'
    

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        print('Trying to connect to find local ip')
        s.connect(('10.255.255.255', 80))
        IP = s.getsockname()[0]
    
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()

    return IP

class UDPSocketState(Enum):
    UNDISCOVERED = 0
    DISCOVERED = 1


class UDPSocket():
    state : UDPSocketState

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)        
        # Listen to ALL network interfaces for broadcasted
        # message from control software
        self.sock.bind(('', 20100))
        self.state = UDPSocketState.UNDISCOVERED

    def mysend(self, server_ip: str, port: int):
        pass

    def myrecv(self):

        MSGLEN = 256

        self.server_ip = None
        self.server_port = None

        chunks = []
        bytes_recd = 0
        while bytes_recd < MSGLEN:
            print('Trying to receive bytes')
            chunk = self.sock.recvfrom(MSGLEN - bytes_recd)
            data = chunk[0]

            self.server_ip = chunk[1][0]
            self.server_port = chunk[1][1]

            if data == b'':
                raise RuntimeError("Empty message")
            
            chunks.append(data)
            bytes_recd += len(data)

            print(f'Read {bytes_recd}/{MSGLEN} bytes')
            print(data)

        return b''.join(chunks)

def main():

    my_socket = UDPSocket()

    while True:
        
        while my_socket.state == UDPSocketState.UNDISCOVERED:
            try:
                raw_msg = my_socket.myrecv()
                code, data = struct.unpack('=H254s', raw_msg)
                received_cmd = Message(code, str(data, 'utf-8').strip('\x00'))

                if code == MessageCode.DISCOVER.value:
                    print('Has been discovered by the server')

                    msg = Message(MessageCode.DOCK_DISCOVER_ACK.value, 'DOCK DISCOVERED')
                    print(f'Writing {msg.to_network_message()}')
                    my_socket.sock.sendto(msg.to_network_message(), (my_socket.server_ip, my_socket.server_port))
                    my_socket.state = UDPSocketState.DISCOVERED
                else:
                    print('Unknown message format received')

            except Exception as ex:
                print(ex)

            time.sleep(1)

        time.sleep(1)
            


    return

if __name__ == '__main__':
    main()
