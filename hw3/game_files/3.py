# tic-tac-toe

import socket
import sys

def game(game_socket, is_server):
    board = [' ' for _ in range(9)]
    current_player = 'X' if is_server else 'O'  # server starts as X

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

                if move < 0 or move > 8 or board[move] != ' ':
                    print("Invalid move. Try again.")
                    continue

                board[move] = current_player
                display_board()

                if check_winner() == current_player:
                    print(f"{current_player} wins!")
                    game_socket.send(b"end")
                    break
                elif is_draw():
                    print("It's a draw!")
                    game_socket.send(b"end")
                    break

                if is_server:
                    game_socket.send(str(move).encode('utf-8'))

                current_player = 'O' if current_player == 'X' else 'X'

            except ValueError:
                print("Invalid input. Enter a number between 0 and 8.")
        else:
            print("Waiting for opponent's move...")
            received_message = game_socket.recv(1024).decode('utf-8')
            if received_message == "end":
                print("Opponent won. Game over!")
                break
            move = int(received_message)

            if move < 0 or move > 8 or board[move] != ' ':
                print("Invalid move received from opponent.")
                continue

            board[move] = current_player
            display_board()

            if check_winner() == current_player:
                print(f"{current_player} wins!")
                game_socket.send(b"end")
                break
            elif is_draw():
                print("It's a draw!")
                game_socket.send(b"end")
                break

            current_player = 'O' if current_player == 'X' else 'X'

if __name__ == "__main__":
    print("3.py running")
    role = sys.argv[1]
    ip = sys.argv[2]
    port = int(sys.argv[3])

    is_server = role == "server"
    game_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        if is_server:
            game_socket.bind((ip, port))
            game_socket.listen(1)
            print("Waiting for opponent to connect...")
            conn, addr = game_socket.accept()
            print(f"Opponent connected from {addr}")
            game(conn, is_server)
        else:
            game_socket.connect((ip, port))
            print("Connected to server.")
            game(game_socket, is_server)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        game_socket.close()
