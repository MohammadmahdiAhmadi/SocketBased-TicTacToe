import socket
import threading
import json
import tictactoe

IN_GAME = False


def gameserver_thread(gameserver_socket):
    while True:
        # Wait for a player to connect
        player1_socket, player1_address = gameserver_socket.accept()
        global IN_GAME
        IN_GAME = True
        change_status('IN_GAME')

        print(f'player connected: {player1_address}')

        while True:
            try:
                # Receive a message from the client
                message = player1_socket.recv(2048).decode()
                if not message:
                    # The client has disconnected
                    print(f'Player disconnected: {player1_address}')
                    # continue

                # Decode the message from JSON format
                message_data = json.loads(message)
                if message_data['request'] == 'start_game_handshake':
                    tictactoe.print_matrix()
                    response_data = {
                        'success': True, 'message': 'I am ready to play', 'data': message_data['data']}
                    player1_socket.sendall(json.dumps(response_data).encode())

                elif message_data['request'] == 'move':
                    tictactoe.matrix = message_data['data']['matrix']
                    tictactoe.print_matrix()
                    tictactoe.get_input(tictactoe.playerTwo)
                    message_data['data']['matrix'] = tictactoe.matrix
                    response_data = {
                        'success': True, 'message': 'I am moved', 'data': message_data['data']}
                    player1_socket.sendall(json.dumps(response_data).encode())

                elif message_data['request'] == 'winner_announcement':
                    tictactoe.matrix = message_data['data']['matrix']
                    tictactoe.print_matrix()
                    if message_data['data']['winner'] == 'draw':
                        print('draw')
                    else:
                        print(
                            f"Player {message_data['data']['winner']} is the winner")
                    tictactoe.clean_matrix()
                    IN_GAME = False
                    change_status('READY_TO_PLAY')
                    break

            except:
                # There was an error receiving the message
                print(f'Error receiving message from {player1_address}')
                break


def get_list():
    get_list_data = {'request': 'get_list', 'data': {}}
    client_socket.sendall(json.dumps(get_list_data).encode())
    response = client_socket.recv(2048).decode()
    response_data = json.loads(response)
    return response_data


def end_game():
    change_status_data = {'request': 'end_game', 'data': {}}
    client_socket.sendall(json.dumps(change_status_data).encode())
    response = client_socket.recv(2048).decode()
    response_data = json.loads(response)
    return response_data


def change_status(new_status):
    """
    READY_TO_PLAY, IN_GAME
    """
    change_status_data = {'request': 'change_status',
                          'data': {'new_status': new_status}}
    client_socket.sendall(json.dumps(change_status_data).encode())
    response = client_socket.recv(2048).decode()
    response_data = json.loads(response)
    return response_data


# Crate client socket to connect to main server
MAINSERVER_HOST = 'localhost'
MAINSERVER_PORT = 1234
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((MAINSERVER_HOST, MAINSERVER_PORT))

# Create gameserver socket for this player (to accept play request by another players)
GAMESERVER_HOST = ''
GAMESERVER_PORT = 0
gameserver_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
gameserver_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
gameserver_socket.bind((GAMESERVER_HOST, GAMESERVER_PORT))
gameserver_socket.listen(1)
GAMESERVER_PORT = gameserver_socket.getsockname()[1]
print(f'Game Server started on {GAMESERVER_HOST}:{GAMESERVER_PORT}')
gameserver_thread = threading.Thread(target=gameserver_thread, args=(gameserver_socket,))
gameserver_thread.start()

# Register the client with the main server
client_name = input('Enter your name: ')
register_data = {'request': 'register', 'data': {
    'name': client_name, 'gameserver_port': GAMESERVER_PORT}}
client_socket.sendall(json.dumps(register_data).encode())
response = client_socket.recv(2048).decode()
response_data = json.loads(response)
print(response_data['message']) if response_data['success'] else print(
    'Registration failed')


while True:
    if IN_GAME:
        continue
    # Send a request to the server
    request = input(
        'Enter request (start_game, end_game): ')
    if request == 'end_game':
        response_data = end_game()
        if response_data['success']:
            print(response_data['message'])
            client_socket.close()
            gameserver_socket.close()
            stop_threads = True
            gameserver_thread.join()
            exit(0)
        else:
            print('end_game failed')

    elif request == 'start_game':
        response_data = get_list()
        if not response_data['success']:
            print('get_list failed')
            continue
        print(
            f'Choose one of this player:\n {response_data["data"]["clients"]}')
        chosen_player_name = input('Enter player name: ')
        player = None
        for client in response_data["data"]["clients"]:
            if client['name'] == chosen_player_name:
                player = client
                break
        if player is None:
            print(f'{chosen_player_name} not found')
            continue

        if player['player_status'] == 'IN_GAME':
            print(
                f'player {player["name"]} alreay in another game. please choose another player.')
            continue

        # Crate player socket to connect to game server
        player_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        player_socket.connect((player['ip'], player['gameserver_port']))

        # Game handshake
        start_game_data = {'request': 'start_game_handshake', 'data': {
            'playerOneName': client_name, 'playerTwoName': player['name'], 'matrix': tictactoe.matrix}}
        player_socket.sendall(json.dumps(start_game_data).encode())
        response = player_socket.recv(2048).decode()
        response_data = json.loads(response)
        if response_data['success']:
            IN_GAME = True
            change_status('IN_GAME')
            result = 0
            i = 0
            tictactoe.print_matrix()
            while result == 0 and i < 9:
                if (i % 2 == 0):
                    tictactoe.get_input(tictactoe.playerOne)
                else:
                    move_data = {'request': 'move', 'data': {
                        'playerOneName': client_name, 'playerTwoName': player['name'], 'matrix': tictactoe.matrix}}
                    player_socket.sendall(json.dumps(move_data).encode())
                    response = player_socket.recv(2048).decode()
                    response_data = json.loads(response)
                    tictactoe.matrix = response_data['data']['matrix']
                    tictactoe.print_matrix()
                result = tictactoe.check_winner()
                i = i + 1
                # print("Current count", i ,result == 0 and i < 9, "Result = ", result)

            if result == 1:
                print(f"Player {client_name} is the winner")
                winner_announcement_data = {'request': 'winner_announcement', 'data': {
                    'playerOneName': client_name, 'playerTwoName': player['name'], 'matrix': tictactoe.matrix, 'winner': client_name}}
            elif result == 2:
                print(f"Player {player['name']} is the winner")
                winner_announcement_data = {'request': 'winner_announcement', 'data': {
                    'playerOneName': client_name, 'playerTwoName': player['name'], 'matrix': tictactoe.matrix, 'winner': player['name']}}
            else:
                print("Draw")
                winner_announcement_data = {'request': 'winner_announcement', 'data': {
                    'playerOneName': client_name, 'playerTwoName': player['name'], 'matrix': tictactoe.matrix, 'winner': 'draw'}}

            player_socket.sendall(json.dumps(
                winner_announcement_data).encode())
            player_socket.close()

            tictactoe.clean_matrix()
            IN_GAME = False
            change_status('READY_TO_PLAY')

        else:
            print('game server is not ready')

    else:
        print('Invalid request')
