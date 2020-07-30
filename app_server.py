import socket
import select
import random
import json

HEADER_LENGTH = 10

PUBLIC_KEYS = []

hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

print(f"Hostname: {hostname}")
print(f"IP Address: {ip_address}")

#This is the IP clients connect to and the server is listening from
IP = '192.168.0.20'
#192.168.0.20
PORT =  4444 #this is an open port clients can connect to

#AF_INET - this refers to some ipv4 uses
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((IP, PORT)) #when a client requests to connect the server binds/connects the IP and PORT of the client

# This makes server listen to new connections
server_socket.listen()

sockets_list = [server_socket]
clients = {}

print(f"Welcome to Group 4 TCP Server.")
print(f'Listening for connections on {IP}:{PORT}...')

#function for getting gcd
def gcd(a, b):
    # getting the gcd of two numbers
    if(b == 0):
        return a
    else:
        return gcd(b, a % b)

#this does the euclidean algorithm
#return gcd, coefficient of a , and coefficient of b
def xgcd(a, b):
    x, old_x = 0, 1
    y, old_y = 1, 0

    while(b != 0):
        quotient = a // b

        a, b = b, a - quotient * b
        old_x, x = x, old_x - quotient * x
        old_y, y = y, old_y - quotient * y

    return a, old_x, old_y

#choooses a random number and checks whether it is co-prime
#that is gcd(e, totient) = 1
def chooseE(totient):
    while True:
        e = random.randrange(2, totient)

        if(gcd(e, totient) == 1):
            return e

#selects two prime numbers from a list of prime numbers
#then generates the public and private keys
def chooseKeys():
    #choose two random numbers
    rand1 = random.randint(100, 300)
    rand2 = random.randint(100, 300)

    fo = open('primes-to-100k.txt', 'r') #open the primes txt recursively
    lines = fo.read().splitlines() #read the files lines
    fo.close() #close the file

    p = int(lines[rand1]) #make the random line selected into an integer after having a random line read
    q = int(lines[rand2]) #same thing again

    #compute n, totient and e
    n = p * q
    totient = (p - 1) * (q - 1)
    e = chooseE(totient)

    return e, n, p, q

PUBLIC_KEYS = chooseKeys()

E = PUBLIC_KEYS[0]
N = PUBLIC_KEYS[1]

print(f"The Public Keys...", "{", E, ",", N, "}")

#convert the list into a json
#when we convert it into a json, we can send an object as bytes over the connection
json_public_keys = json.dumps(PUBLIC_KEYS)

#this function facilitates receiving messages from the a client socket
def receive_message(client_socket):
    try:
        message_header = client_socket.recv(HEADER_LENGTH)

        # for gracefully closing a connection
        if not len(message_header):
            return False

        # Convert header to int value
        message_length = int(message_header.decode('utf-8').strip())

        # Return an object of message header and message data
        return {'header': message_header, 'data': client_socket.recv(message_length)}

    except:
        # client closed connection violently, for example by pressing ctrl+c on his script
        return False

#implementation of select system calls which checks and tells the program when a message has been sent
while True:
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)
    for notified_socket in read_sockets:
        if notified_socket == server_socket:
            client_socket, client_address = server_socket.accept() #accept new connection
            
            #we send the public keys, which includes e, n, p, q to a client
            client_socket.send(bytes(json_public_keys, encoding='utf8')) 

            user = receive_message(client_socket)
            sockets_list.append(client_socket)
            clients[client_socket] = user

            # this prints the client address and username
            print('Accepted new connection from {}:{}, username: {}'.format(*client_address, user['data'].decode('utf-8')))
       
        # Else existing socket is sending a message
        else:
            # Receive message
            message = receive_message(notified_socket)

            # If False, client disconnected, cleanup
            if message is False:
                print('Closed connection from: {}'.format(clients[notified_socket]['data'].decode('utf-8')))

                # Remove from list for socket.socket()
                sockets_list.remove(notified_socket)

                # Remove from our list of users
                del clients[notified_socket]

                continue

            # Get user by notified socket, so we will know who sent the message
            user = clients[notified_socket]

            print(f'Received message from {user["data"].decode("utf-8")}: {message["data"].decode("utf-8")}')

            # Iterate over connected clients and broadcast message
            for client_socket in clients:
                # But don't sent it to sender
                if client_socket != notified_socket:

                    # Send user and message (both with their headers)
                    # We are reusing here message header sent by sender, and saved username header send by user when he connected
                    client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])
                    
    # It's not really necessary to have this, but will handle some socket exceptions just in case
    for notified_socket in exception_sockets:

        # Remove from list for socket.socket()
        sockets_list.remove(notified_socket)

        # Remove from our list of users
        del clients[notified_socket]