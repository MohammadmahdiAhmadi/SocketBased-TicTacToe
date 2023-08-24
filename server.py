import socket
import threading
import json
import random
import time

HOST = ''
PORT = 1234

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print(f'Server started on {HOST}:{PORT}')

clients = {}


def client_thread(client_socket, client_address):
    print(f'Client connected: {client_address}')

    while True:
        try:
            # Receive a message from the client
            message = client_socket.recv(2048).decode()
            if not message:
                # The client has disconnected
                print(f'Client disconnected: {client_address}')
                # continue

            # Decode the message from JSON format
            message_data = json.loads(message)
            print(f'Received from {client_address}: {message_data}')

            # Check the type of request and handle accordingly
            if message_data['request'] == 'register':
                # Register the client
                random.seed(time.time())
                client_name = message_data['data']['name'] + \
                    str(random.randint(1, 10))
                client_info = {
                    'name': client_name,
                    'player_status': "READY_TO_PLAY",
                    'ip': client_address[0],
                    'gameserver_port': message_data['data']['gameserver_port']
                }
                clients[client_socket] = client_info
                print(f'{client_name} registered with server')

                # Send success message to client
                response_data = {
                    'success': True, 'message': f'{client_name} registered successfully', 'data': {}}
                client_socket.sendall(json.dumps(response_data).encode())

            elif message_data['request'] == 'get_list':
                # Send list of clients to client
                client_list = []
                for client_socket_, client_info in clients.items():
                    if client_socket_ == client_socket:
                        continue
                    client_list.append(client_info)

                response_data = {'success': True, 'message': '',
                                 'data': {'clients': client_list}}
                client_socket.sendall(json.dumps(response_data).encode())

            elif message_data['request'] == 'end_game':
                response_data = {'success': True,
                                 'message': 'end game successfuly', 'data': {}}
                client_socket.sendall(json.dumps(response_data).encode())

                # Close connection and remove from dict
                clients.pop(client_socket)
                client_socket.close()

            elif message_data['request'] == 'change_status':
                # Change status of the client
                clients[client_socket]['player_status'] = message_data['data']['new_status']

                response_data = {'success': True, 'message': 'Changing status successfuly', 'data': {
                    'client': clients[client_socket]}}
                client_socket.sendall(json.dumps(response_data).encode())

        except:
            # There was an error receiving the message
            print(f'Error receiving message from {client_address}')
            break


while True:
    # Wait for a client to connect
    client_socket, address = server_socket.accept()

    # Start a new thread to handle the client
    threading.Thread(target=client_thread, args=(
        client_socket, address)).start()
