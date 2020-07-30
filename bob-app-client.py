import socket
import select
import errno
import json


HEADER_LENGTH = 10
block_size = 2

hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

print(f"Hostname: {hostname}")
print(f"IP Address: {ip_address}")

IP = "192.168.0.20"
PORT = 4444
my_username = "Bob"

#creating a socket, AF_INET is ipv4, 
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((IP, PORT))
json_public_keys = client_socket.recv(128) #the recv function works in bytes so 128bytes is 1024 bits

#turning the received json string from json to python list
python_public_keys = json.loads(json_public_keys) 

E = python_public_keys[0]
N = python_public_keys[1]
P = python_public_keys[2]
Q = python_public_keys[3]

client_socket.setblocking(False)

username = my_username.encode('utf-8') #encoding username in bytes
username_header = f"{len(username):<{HEADER_LENGTH}}".encode('utf-8')
client_socket.send(username_header + username)

def gcd(a, b):
    # getting the gcd of two numbers
    if(b == 0):
        return a
    else:
        return gcd(b, a % b)

def xgcd(a, b):
    #this does the euclidean algorithm
    #return gcd, coefficient of a , and coefficient of b

    x, old_x = 0, 1
    y, old_y = 1, 0

    while(b != 0):
        quotient = a // b

        a, b = b, a - quotient * b
        old_x, x = x, old_x - quotient * x
        old_y, y = y, old_y - quotient * y

    return a, old_x, old_y

def generate_private_key(p, q, e, n):
    totient = (p-1) * (q-1)
    gcd, x, y = xgcd(e, totient)

    #making sure d is positive
    if(x < 0):
        d = x + totient
    else:
        d = x
    
    return d

D = generate_private_key(P, Q, E, N)
print("Here's Bob's private key: ", "{", D, ",", N, "}")

def encrypt(message, n, e, block_size):
    #we encrypt a message - string by raising each characters ASCII value to the power of e and taking the modulus of n.
    #this returns a string of numbers 

    #block_size refers to how many characters makeup one group of numbers in each index of encrypted_blocks

    encrypted_blocks = []
    ciphertext = -1 

    if (len(message) > 0):
        #initialize ciphertext to the ASCII of the first character of message
        ciphertext = ord(message[0]) #the ord() function in python gives the corresponding unicode represenation of that character/letter

    for i in range(1, len(message)):
        #add ciphertext to the list if the max block size is reached
        #reset the ciphertext so we can continue adding ASCII codes
        if( i % block_size == 0):
            encrypted_blocks.append(ciphertext)
            ciphertext = 0
        
        ciphertext = ciphertext * 1000 + ord(message[i])
    
    encrypted_blocks.append(ciphertext) #we now push the unicode values to the encryptd_blocks list

    #encrypted all the numbers by taking them to the power e & modding it by n
    for i in range(len(encrypted_blocks)):
        encrypted_blocks[i] = str((encrypted_blocks[i] ** e) % n)
    
    #create a string from the number
    encrypted_message = " ".join(encrypted_blocks)

    return encrypted_message

def decrypt(n, d, blocks, block_size = 2):
    # turns the string into a list of ints
    list_blocks = blocks.split(' ')
    int_blocks = []

    for s in list_blocks:
        int_blocks.append(int(s))

    message = ""

    # converts each int in the list to block_size number of characters
    # by default, each int represents two characters
    for i in range(len(int_blocks)):
        # decrypt all of the numbers by taking it to the power of d
        # and modding it by n
        int_blocks[i] = (int_blocks[i]**d) % n
        
        tmp = ""
        # take apart each block into its ASCII codes for each character
        # and store it in the message string
        for c in range(block_size):
            tmp = chr(int_blocks[i] % 1000) + tmp
            int_blocks[i] //= 1000
        message += tmp

    return message


while True:
    # user inputs a message
    message = input(f'{my_username} > ')
    #  If message is not empty - send it
    if message:
        # Encode message to bytes, prepare header and convert to bytes, like for username above, then send
        message = bytes(encrypt(message, N, E, block_size), encoding='utf8')#.encode('utf-8')
        message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
        client_socket.send(message_header + message)

    # Now we want to loop over received messages (there might be more than one) and print them
    try:
        while True:

            # Receive our "header" containing username length, it's size is defined and constant
            username_header = client_socket.recv(HEADER_LENGTH)

            # If we received no data, server gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
            if not len(username_header):
                print('Connection closed by the server')
                sys.exit()

            # Convert header to int value
            username_length = int(username_header.decode('utf-8').strip())

            # Receive and decode username
            username = client_socket.recv(username_length).decode('utf-8')

            # Now do the same for message (as we received username, we received whole message, there's no need to check if it has any length)
            message_header = client_socket.recv(HEADER_LENGTH)
            message_length = int(message_header.decode('utf-8').strip())
            message = client_socket.recv(message_length).decode('utf-8')

            # Print message
            print(f'{username} > {decrypt(N, D, message, block_size)}')

    # this is error handling both for the OS and non-regular expressions
    except IOError as e:
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print('Reading error: {}'.format(str(e)))
            sys.exit()

        # We just did not receive anything
        continue

    except Exception as e:
        # Any other exception - something happened, exit
        print('Reading error: '.format(str(e)))
        sys.exit()