# client.py

import socket
import threading
import time
import sys
import select

user_data = {}
server_port = 10007
first = True
stop_listener = threading.Event()
invitation_active = threading.Event()
in_game = False

def start():
    global server_port, first
    while True:
        client_s = connect2server()
        if not client_s:
            continue  # Retry connection if it fails initially
        while True:
            command = input("Login/Register: ")
            if command == "register":
                register(client_s)
                break
            elif command == "login":
                if login(client_s):  # logged in
                    if not user_session(client_s):  # logged out
                        break
                else:
                    break
            else:
                print("Invalid command. Please enter 'login' or 'register'.")
                break
        client_s.close()

def connect2server():
    global first, server_port
    while True:
        client_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            if first:
                server_port = int(input("Enter the port server is running on: "))
                first = False
            client_s.connect(('140.113.235.152', server_port))
            return client_s
        except (ConnectionRefusedError, socket.error):
            print("Unable to connect to server. Please ensure the server is running.")
            first = True
            client_s.close()
            time.sleep(2)

def register(client_s):
    try:
        client_s.send(b"register")
        while True:
            response = client_s.recv(1024).decode('utf-8')
            if response == "u":
                client_s.send(input("username: ").encode('utf-8'))
            elif response == "p":
                client_s.send(input("password: ").encode('utf-8'))
            elif response == "error":
                print("Username already exists.")
                return
            elif response == "ok":
                print("Registration successful. Please login.")
                return
    except (ConnectionResetError, socket.error):
        print("Connection to the server was lost during registration.")

def login(client_s):
    try:
        client_s.send(b"login")
        while True:
            response = client_s.recv(1024).decode('utf-8')
            if response == "u":
                client_s.send(input("username: ").encode('utf-8'))
            elif response == "p":
                client_s.send(input("password: ").encode('utf-8'))
            elif response == "error-u":
                print("User doesn't exist. Please register first.")
                return False
            elif response == "error-p":
                print("Incorrect password.")
                return False
            elif response == "ok":
                print(client_s.recv(1024).decode('utf-8'))
                return True
    except (ConnectionResetError, socket.error):
        print("Connection to the server was lost during login.")
        return False

def user_session(client_s):
    listener_thread = threading.Thread(target=listen_for_invitation, args=(client_s,))
    listener_thread.start()

    while True:
        if in_game:
            time.sleep(3)
            continue
        if not invitation_active.is_set():
            print("\n> ", end='', flush=True)
            ready, _, _ = select.select([sys.stdin], [], [], 10)

            if ready:
                command = sys.stdin.readline().strip()
                if command == "logout":
                    stop_listener.set()
                    listener_thread.join()
                    if logout(client_s):
                        return False
                elif command == "c":
                    stop_listener.set()
                    listener_thread.join()
                    create(client_s)
                    stop_listener.clear()
                    listener_thread = threading.Thread(target=listen_for_invitation, args=(client_s,))
                    listener_thread.start()
                elif command == "j":
                    stop_listener.set()
                    listener_thread.join()
                    join(client_s)
                    stop_listener.clear()
                    listener_thread = threading.Thread(target=listen_for_invitation, args=(client_s,))
                    listener_thread.start()
                else:
                    print("Invalid command. Use 'logout', 'j' to join a room, or 'c' to create a room.")
            else:
                time.sleep(1)
        else:
            time.sleep(1)

def logout(client_s):
    try:
        client_s.send(b"logout")
        response = client_s.recv(1024).decode('utf-8')
        if response == "ok":
            print("Logged out. Redirecting to log in page...")
            user_data.clear()
            return True
        elif response == "error":
            print("Error. Please try again")
            return False
    except (ConnectionResetError, socket.error):
        print("Connection to the server was lost during logout.")
        return False

def create(client_s):
    try:
        client_s.send(b"c")
        response = client_s.recv(1024).decode('utf-8')
        if response == "error":
            print("Status not idle, cannot create room, redirecting...")
            return
        elif response == "ok":
            command = input("public room or private room [1/2]: ")
            if command == "1":
                create_public(client_s)
            elif command == "2":
                create_private(client_s)
    except (ConnectionResetError, socket.error):
        print("Error while creating room. Connection lost.")

def create_public(client_s): 
    try:
        client_s.send(b"cpb")
        while True:
            response = client_s.recv(1024).decode('utf-8')
            if response == "gt":
                game_12 = input("Enter game type [1/2]: ")
                client_s.send(game_12.encode('utf-8'))
            elif response == "p":
                game_ip, game_port = input("Enter ip:port for game server: ").split(":")
                client_s.send(f"{game_ip}:{game_port}".encode('utf-8'))
                continue
            elif response == "ok":
                start_game_server(client_s, game_ip, int(game_port), game_12)
                return
            else:
                print("Error creating public room.")
                return
    except (ConnectionResetError, socket.error):
        print("Error: Lost connection to the server while creating public room.")
    except Exception as e:
        print(f"Unexpected error while creating public room: {e}")


def join(client_s):
    try:
        client_s.send(b"j")
        statuscheck = client_s.recv(1024).decode('utf-8')
        if statuscheck == "error":
            print("User not idle. Cannot join room")
            return
        rooms = client_s.recv(1024).decode('utf-8')
        if rooms == "no":
            print("No available rooms.")
            return
        print(f"{rooms}")
        client_s.send(input("Enter room ID to join: ").encode('utf-8'))
        response = client_s.recv(1024).decode('utf-8')
        if response.startswith("ok:"):
            _, ip, port, game_12 = response.split(":")
            game_client_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            game_client_s.connect((ip, int(port)))
            print(f"Joining game at {ip}:{port}")
            start_game_client(client_s, game_client_s, game_12)
    except (ConnectionResetError, socket.error):
        print("Error: Lost connection to the server while joining the room.")
    except Exception as e:
        print(f"Unexpected error while joining room: {e}")


def create_private(client_s):
    try:
        client_s.send(b"cpv")
        while True:
            response = client_s.recv(1024).decode('utf-8')
            if response == "gt":
                game_12 = input("Enter game type [1/2]: ")
                client_s.send(game_12.encode('utf-8'))
            elif response == "cpvok":
                invite_player(client_s, game_12)
                return
            else:
                print("Error creating private room.")
                return
    except (ConnectionResetError, socket.error):
        print("Error: Lost connection to the server while creating private room.")
    except Exception as e:
        print(f"Unexpected error while creating private room: {e}")


def invite_player(client_s, game_12):
    try:
        player = input("Enter username to invite: ")
        client_s.send(f"inv {player}".encode('utf-8'))
        response = client_s.recv(1024).decode('utf-8')
        if response == "i-ok":
            print(f"Invitation sent to {player}...")
            time.sleep(3)
            response = client_s.recv(1024).decode('utf-8')
            if response == "ac":
                game_ip, game_port = input("Enter ip:port for game server: ").split(":")
                client_s.send(f"{game_ip}:{game_port}".encode('utf-8'))           
                print(f"{player} accepted the invitation, waiting for connection...")
                start_game_server(client_s, game_ip, int(game_port), game_12)
        elif response == "error":
            print(f"Failed to invite {player}. Check if they are idle.")
    except (ConnectionResetError, socket.error):
        print("Error: Lost connection to the server while inviting player.")
    except Exception as e:
        print(f"Unexpected error while inviting player: {e}")


def listen_for_invitation(client_s):
    while not stop_listener.is_set():
        try:
            client_s.settimeout(1.0)
            message = client_s.recv(1024).decode('utf-8')
            if message.startswith("Invitation"):
                invitation_active.set()
                print(message)
                if handle_invitation(client_s):
                    invitation_active.clear()
            elif message.startswith("ok:"):
                _, ip, port, game_12 = message.split(":")
                game_client_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                game_client_s.connect((ip, int(port)))
                print(f"Joining game at {ip}:{port}")
                start_game_client(client_s, game_client_s, game_12)
                invitation_active.clear()
                stop_listener.set()
            else:
                print(message)
        except (socket.timeout, ConnectionResetError, socket.error):
            print("Connection to the server was lost.")
            break

def handle_invitation(client_s):
    try:
        command = input("Accept invitation? [y/n]: ")
        if command == "y":
            client_s.send(b"yes")
            ip_port = client_s.recv(1024).decode('utf-8')
            print(f"Received IP and port: {ip_port}")
            _, ip, port = ip_port.split(":")
            print(f"Connecting to game at {ip}:{port}")
            
            game_client_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            game_client_s.connect((ip, int(port)))
            print("Connected to the game.")
        else:
            client_s.send(b"no")
            print("Invitation declined.")
        return True
    except (ConnectionResetError, socket.error):
        print("Error: Lost connection to the server while handling invitation.")
        return False

def start_game_server(client_s, game_ip, game_port, game_12):
    global in_game
    in_game = True
    try:
        game_serv_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        game_serv_s.bind((game_ip, game_port))
        game_serv_s.listen(1)
        print(f"Game server started at port {game_port}, waiting for player to connect...")

        game_client_s, game_client_addr = game_serv_s.accept()
        print(f"Player connected from {game_client_addr}")

        if game_12 == "1":
            game1(game_client_s, True)
        else:
            game2(game_client_s, True)

        game_client_s.close()
        game_serv_s.close()
        client_s.send(b"end")
    except (ConnectionResetError, socket.error):
        print("Error: Lost connection to the server while setting up the game server.")
    except Exception as e:
        print(f"Unexpected error in game server: {e}")
    finally:
        in_game = False

def start_game_client(client_s, game_client_s, game_12):
    global in_game
    in_game = True
    try:
        if game_12 == "1":
            game1(game_client_s, False)
        else:
            game2(game_client_s, False)

        game_client_s.close()
        client_s.send(b"end")
    except (ConnectionResetError, socket.error):
        print("Error: Lost connection to the server during the game.")
    except Exception as e:
        print(f"Unexpected error in game client: {e}")
    finally:
        in_game = False


def game1(game_socket, is_server):
    board = [' ' for _ in range(9)]
    current_player = 'X' if is_server else 'O'  # Server starts as 'X'

    def display_board():
        print("\n")
        print(f"{board[0]} | {board[1]} | {board[2]}")
        print("--+---+--")
        print(f"{board[3]} | {board[4]} | {board[5]}")
        print("--+---+--")
        print(f"{board[6]} | {board[7]} | {board[8]}")
        print("\n")

    def check_winner():
        win_combinations = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6)
        ]
        for a, b, c in win_combinations:
            if board[a] == board[b] == board[c] != ' ':
                return board[a]
        return None

    def is_draw():
        return ' ' not in board

    display_board()
    while True:
        if (is_server and current_player == 'X') or (not is_server and current_player == 'O'):
            # Current player's turn
            try:
                if is_server:
                    move = int(input("Enter your move (0-8): "))
                else:
                    print("Waiting for opponent's move...")
                    received_message = game_socket.recv(1024).decode('utf-8')
                    if received_message == "end":
                        print("Opponent won. Game over!")
                        break
                    move = int(received_message)

                # Validate and apply move
                if board[move] != ' ':
                    print("Invalid move. Try again.")
                    continue
                board[move] = current_player
                display_board()

                # Check for winner or draw
                if check_winner() == current_player:
                    print(f"{current_player} wins!")
                    game_socket.send(b"end")  # Signal end of game
                    break
                elif is_draw():
                    print("It's a draw!")
                    game_socket.send(b"end")  # Signal end of game
                    break

                # Send move to the opponent if this side is the server
                if is_server:
                    game_socket.send(str(move).encode('utf-8'))

                # Alternate turn
                current_player = 'O' if current_player == 'X' else 'X'

            except ValueError:
                print("Invalid input. Enter a number between 0 and 8.")
        else:
            # Opponent's turn
            if is_server:
                print("Waiting for opponent's move...")
                received_message = game_socket.recv(1024).decode('utf-8')
                if received_message == "end":
                    print("Opponent won. Game over!")
                    break
                move = int(received_message)
            else:
                move = int(input("Enter your move (0-8): "))

            # Validate and apply move
            if board[move] != ' ':
                print("Invalid move. Try again.")
                continue
            board[move] = current_player
            display_board()

            # Check for winner or draw
            if check_winner() == current_player:
                print(f"{current_player} wins!")
                game_socket.send(b"end")  # Signal end of game
                break
            elif is_draw():
                print("It's a draw!")
                game_socket.send(b"end")  # Signal end of game
                break

            # Send move to the opponent if this side is the client
            if not is_server:
                game_socket.send(str(move).encode('utf-8'))

            # Alternate turn
            current_player = 'O' if current_player == 'X' else 'X'


def game2(game_socket, is_server):
    # Connect Four-like game implementation
    columns = 7
    rows = 6
    board = [[' ' for _ in range(columns)] for _ in range(rows)]
    current_player = 'X' if is_server else 'O'  # Server starts as 'X'

    def display_board():
        print("\n")
        for row in board:
            print(" | ".join(row))
            print("-" * (columns * 4 - 1))
        print("  ".join(str(i) for i in range(columns)))
        print("\n")

    def check_winner():
        # Check horizontal, vertical, and diagonal for 4 in a row
        for r in range(rows):
            for c in range(columns - 3):
                if board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3] != ' ':
                    return board[r][c]
        for r in range(rows - 3):
            for c in range(columns):
                if board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c] != ' ':
                    return board[r][c]
        for r in range(rows - 3):
            for c in range(columns - 3):
                if board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3] != ' ':
                    return board[r][c]
            for c in range(3, columns):
                if board[r][c] == board[r+1][c-1] == board[r+2][c-2] == board[r+3][c-3] != ' ':
                    return board[r][c]
        return None

    def drop_piece(col, piece):
        for r in range(rows-1, -1, -1):
            if board[r][col] == ' ':
                board[r][col] = piece
                return

    display_board()
    while True:
        # Server's turn if it's the server's move or client's move if it's the client's turn
        if (is_server and current_player == 'X') or (not is_server and current_player == 'O'):
            try:
                if is_server:
                    move = int(input("Enter column (0-6): "))
                else:
                    print("Waiting for opponent's move...")
                    received_message = game_socket.recv(1024).decode('utf-8')
                    if received_message == "end":
                        print("Opponent won. Game over!")
                        break
                    move = int(received_message)

                # Validate move and apply
                if move < 0 or move >= columns or board[0][move] != ' ':
                    print("Invalid move. Try again.")
                    continue

                drop_piece(move, current_player)
                display_board()

                # Check for winner or draw
                if check_winner() == current_player:
                    print(f"{current_player} wins!")
                    game_socket.send(b"end")  # Signal end of game
                    break

                # Send move to opponent
                if is_server:
                    game_socket.send(str(move).encode('utf-8'))

                # Alternate turn
                current_player = 'O' if current_player == 'X' else 'X'

            except ValueError:
                print("Invalid input. Enter a number between 0 and 6.")
        else:
            # Opponent's turn
            if is_server:
                print("Waiting for opponent's move...")
                received_message = game_socket.recv(1024).decode('utf-8')
                if received_message == "end":
                    print("Opponent won. Game over!")
                    break
                move = int(received_message)
            else:
                move = int(input("Enter column (0-6): "))

            # Validate and apply move
            if move < 0 or move >= columns or board[0][move] != ' ':
                print("Invalid move. Try again.")
                continue
            drop_piece(move, current_player)
            display_board()

            # Check for winner or draw
            if check_winner() == current_player:
                print(f"{current_player} wins!")
                game_socket.send(b"end")  # Signal end of game
                break

            # Send move to the opponent if this side is the client
            if not is_server:
                game_socket.send(str(move).encode('utf-8'))

            # Alternate turn
            current_player = 'O' if current_player == 'X' else 'X'


if __name__ == "__main__":
    start()
