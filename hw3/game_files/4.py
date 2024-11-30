# connect four
import socket
import sys

def game(game_socket, is_server):
    columns = 7
    rows = 6
    board = [[' ' for _ in range(columns)] for _ in range(rows)]
    current_player = 'X' if is_server else 'O'  # server starts as x

    def display_board():
        print("\n")
        for row in board:
            print(" | ".join(row))
            print("-" * (columns * 4 - 1))
        print("  ".join(str(i) for i in range(columns)))
        print("\n")

    def check_winner():
        # check horizontal, vertical, diagonal
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

                if move < 0 or move >= columns or board[0][move] != ' ':
                    print("Invalid move. Try again.")
                    continue

                drop_piece(move, current_player)
                display_board()

                # check winner, draw
                if check_winner() == current_player:
                    print(f"{current_player} wins!")
                    game_socket.send(b"end") 
                    break

                if is_server:
                    game_socket.send(str(move).encode('utf-8'))

                current_player = 'O' if current_player == 'X' else 'X'

            except ValueError:
                print("Invalid input. Enter a number between 0 and 6.")
        else:
            if is_server:
                print("Waiting for opponent's move...")
                received_message = game_socket.recv(1024).decode('utf-8')
                if received_message == "end":
                    print("Opponent won. Game over!")
                    break
                move = int(received_message)
            else:
                move = int(input("Enter column (0-6): "))

            if move < 0 or move >= columns or board[0][move] != ' ':
                print("Invalid move. Try again.")
                continue
            drop_piece(move, current_player)
            display_board()

            if check_winner() == current_player:
                print(f"{current_player} wins!")
                game_socket.send(b"end")
                break
            
            if not is_server:
                game_socket.send(str(move).encode('utf-8'))

            current_player = 'O' if current_player == 'X' else 'X'



if __name__ == "__main__":
    print("4.py running")
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
