# client.py

import socket
import time
import threading
import os
import ast
import select
import sys
import queue
import shutil
import subprocess

# connect2server
server_port = 10007
first = True
# listener
stop_listener = threading.Event()
message_active = threading.Event()
message_queue = queue.Queue()
in_game = False
# own data
invitation_table = {}
username = None

def start():
    global server_port, first
    while True:
        client_s = connect2server()
        if not client_s:
            continue
        while True:
            command = input("(1) register\n(2) login\nPlease enter command [1/2]: ")
            if command == "1":
                register(client_s)
                break                  
            elif command == "2":
                if login(client_s):
                    #print("--------LOBBY--------\n(1) create game room\n(2) join game room\n(3) list online players\n(4) list game rooms\n(5) list game types\n(6) invitation management\n(7) game development management\n(8) logout\nPlease enter command [1/2/3/4/5/6/7/8]: ", end='')
                    if not session(client_s):
                        break
                else:
                    break
            else:
                print("Invalid command.\n(1) register\n(2) login\nPlease enter command [1/2]: ")

def connect2server():
    global server_port, first
    while True:
        client_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            if first:
                server_port = int(input("Enter port server is running on: "))
                first = False
            client_s.connect(('140.113.235.151', server_port))
            return client_s
        except(ConnectionError, socket.error):
            print("Unable to connect to server.")
            first = True
            client_s.close()
            time.sleep(2)
            
def register(client_s):
    try:
        client_s.send(b"register")
        while True:
            response = client_s.recv(1024).decode('utf-8')
            if response == "reg-usr":
                client_s.send(input("username: ").encode('utf-8'))
            elif response == "reg-psw":
                client_s.send(input("password: ").encode('utf-8'))
            elif response == "reg-err":
                print("Username already exists.")
                break
            elif response == "reg-ok":
                print("Registration successful. Please login.")
                break
    except(ConnectionError, socket.error, socket.timeout):
        print("Error: connection to server lost")
        
def login(client_s):
    global username
    try:
        client_s.send(b"login")
        while True:
            response = client_s.recv(1024).decode('utf-8')
            if response == "in-usr":
                username = input("username: ")
                client_s.send(username.encode('utf-8'))
            elif response == "in-psw":
                client_s.send(input("password: ").encode('utf-8'))
            elif response == "in-err-usr":
                print("User doesn't exist. Please register first.")
                return False
            elif response == "in-err-psw":
                print("Incorrect password.")
                return False
            elif response == "in-ok":
                print(client_s.recv(1024).decode('utf-8'))
                return True
    except (ConnectionResetError, socket.error):
        print("Connection to the server was lost during login.")
        return False

def session(client_s):
    listener_thread = threading.Thread(target=listener, args=(client_s,))
    listener_thread.start()
    prompt = True
    while True:
        if in_game:
            time.sleep(3)
            continue
        if not message_active.is_set():
            if prompt:
                print("\n--------LOBBY--------\n"
                      "(1) create game room\n"
                      "(2) join public room\n"
                      "(3) list online players\n"
                      "(4) list game rooms\n"
                      "(5) list game types\n"
                      "(6) invitation management\n"
                      "(7) game development management\n"
                      "(8) logout\n"
                      "Please enter command [1/2/3/4/5/6/7/8]: ", end='')
                prompt = False
            ready, _, _ = select.select([sys.stdin], [], [], 0.5)
            if not ready and message_queue.empty():
                continue
            while not message_queue.empty():
                message = message_queue.get()
                print("\n",message)
                prompt = True
            if ready:
                command = sys.stdin.readline().strip()
                prompt = True
                handle_command(client_s, command, listener_thread)

def handle_command(client_s, command, listener_thread):
    global in_game
    stop_listener.set()
    listener_thread.join()

    if command == "1":
        create_room(client_s)
    elif command == "2":
        join_pub_room(client_s)
    elif command == "3":
        list_players(client_s)
    elif command == "4":
        list_rooms(client_s)
    elif command == "5":
        list_games(client_s)
    elif command == "6":
        invitation_management(client_s)
    elif command == "7":
        game_dev_management(client_s)
    elif command == "8":
        if logout(client_s):
            return False
    else:
        print("Invalid command.")
    stop_listener.clear()
    listener_thread = threading.Thread(target=listener, args=(client_s,))
    listener_thread.start()

def listener(client_s):
    while not stop_listener.is_set():
        try:
            client_s.settimeout(1.0)
            message = client_s.recv(1024).decode('utf-8')
            if message:
                message_queue.put(message)
        except (socket.timeout, ConnectionResetError, socket.error):
            continue

"""
def session(client_s):
    listener_thread = threading.Thread(target=listener, args=(client_s,))
    listener_thread.start()
    prompt = True
    while True:
        if in_game:
            time.sleep(3)
            continue
        if not message_active.is_set():
            if prompt:
                print("\n--------LOBBY--------\n(1) create game room\n(2) join public room\n(3) list online players\n(4) list game rooms\n(5) list game types\n(6) invitation management\n(7) game development management\n(8) logout\nPlease enter command [1/2/3/4/5/6/7/8]: ", end='')
                prompt = False
            ready, _, _=select.select([sys.stdin], [], [], 5)
            if ready:                 
                command = sys.stdin.readline().strip()
                prompt = True
                if command == "1":
                    stop_listener.set()
                    listener_thread.join()
                    create_room(client_s)
                    stop_listener.clear()
                    listener_thread = threading.Thread(target=listener, args=(client_s,))
                    listener_thread.start()
                elif command == "2":
                    stop_listener.set()
                    listener_thread.join()
                    join_pub_room(client_s)
                    stop_listener.clear()
                    listener_thread = threading.Thread(target=listener, args=(client_s,))
                    listener_thread.start()
                elif command == "3":
                    stop_listener.set()
                    listener_thread.join()
                    list_players(client_s)
                    stop_listener.clear()
                    listener_thread = threading.Thread(target=listener, args=(client_s,))
                    listener_thread.start()
                elif command == "4":
                    stop_listener.set()
                    listener_thread.join()
                    list_rooms(client_s)
                    stop_listener.clear()
                    listener_thread = threading.Thread(target=listener, args=(client_s,))
                    listener_thread.start()
                elif command == "5":
                    stop_listener.set()
                    listener_thread.join()
                    list_games(client_s)
                    stop_listener.clear()
                    listener_thread = threading.Thread(target=listener, args=(client_s,))
                    listener_thread.start()
                elif command == "6":
                    stop_listener.set()
                    listener_thread.join()
                    invitation_management(client_s)
                    stop_listener.clear()
                    listener_thread = threading.Thread(target=listener, args=(client_s,))
                    listener_thread.start()
                elif command == "7":
                    stop_listener.set()
                    listener_thread.join()
                    game_dev_management(client_s)
                    stop_listener.clear()
                    listener_thread = threading.Thread(target=listener, args=(client_s,))
                    listener_thread.start()
                elif command == "8":
                    stop_listener.set()
                    listener_thread.join()
                    if logout(client_s):
                        return False
                else:
                    print("Invalid command.")  
            else:
                time.sleep(1)
        else:
            time.sleep(1)    

def listener(client_s):
    while not stop_listener.is_set():
        try:
            client_s.settimeout(1.0)
            message = client_s.recv(1024).decode('utf-8')
            if message.startswith("inv"):
                message_active.set()
                print("\n" + message)
                print("message")
                message_active.clear()
            else:
                print("messagee")
                print(message)
        except (socket.timeout, ConnectionResetError, socket.error):
            print("lost")
            break
    
"""                

# ------------create room------------------          
def create_room(client_s):
    client_s.send(b"create")
    client_s.send(input("(1) public room\n(2) private room\nPlease enter command [1/2]: ").encode('utf-8'))
    while True:
        gamename = input("Enter game name or press h to list games: ")
        if gamename == "l":
            list_games(client_s)
            continue
        else:
            client_s.send(f"{gamename}".encode('utf-8'))
            response = client_s.recv(1024).decode('utf-8')
            if response == "cre-err-g":
                print("Game not available.")
                continue
            elif response == "cre-ok":
                print("Room created.")
                room_id = client_s.recv(1024).decode('utf-8')
                in_room(client_s, room_id)
                break

def in_room(client_s, room_id):
    while True:
        command = input("\n-----ROOM-----\n(1) invite players\n(2) start game\n(3) change game\n(4) leave\nPlease enter command: ")
        if command == "1":
            invite_player(client_s, room_id)
        elif command == "2":
            start_game(client_s, room_id)
        elif command == "3":
            change_game(client_s, room_id)
        elif command == "4": 
            # if is host, handle host
            # also handle participant
            # errrrrrr
            client_s.send(b"leave")
            client_s.send(room_id.encode('utf-8'))
            response = client_s.recv(1024).decode('utf-8')
            if response == "lv-ok":
                break 
            else:
                print(f"error, {response}")
        else:
            print("Invalid command.")

def invite_player(client_s, room_id):
    while True:
        command = input("\n---invite players---\n(1) invite players\n(2) list idle players\n(3) back to room\nPlease enter command [1/2/3]: ")
        if command == "1":
            client_s.send(b"invite")
            client_s.send(b"inv-usr")
            invitee = input("Enter username to invite: ")
            client_s.send(f"{invitee}".encode('utf-8'))
            while True:
                response = client_s.recv(1024).decode('utf-8')
                if response == "inv-err-usr":
                    print("Error: player not idle")
                    break
                elif response == "inv-id":
                    client_s.send(room_id.encode('utf-8'))
                elif response == "inv-ok":
                    print(f"Invitation sent to {invitee}.") 
                    break                            
        elif command == "2":
            list_players(client_s)
        elif command == "3":
            break
        else:
            print("Invalid command.")
    return

def start_game(client_s, room_id):
    client_s.send(b"start-game")
    username = client_s.recv(1024).decode('utf-8')
    print(username)
    client_s.send(room_id.encode('utf-8'))
    role = client_s.recv(1024).decode('utf-8')
    print(role)
    if role == "host":
        print("host")
        while True:
            response = client_s.recv(1024).decode('utf-8')
            if response == "strt-err-ppl":
                print("Room not full yet. Cannot start game.")
                break
            elif response == "strt-addr":
                room_port = int(find_available_port())
                room_ip = client_s.getsockname()[0]
                room_addr = (room_ip, room_port)
                client_s.send(f"{room_addr}".encode('utf-8'))
            elif response == "strt-ok":
                gamename = client_s.recv(1024).decode('utf-8')
                print(gamename)
                game_file_path = os.path.join("game_files", gamename)
                user_file_path = os.path.join("user", username, "games", gamename)
                shutil.copy(game_file_path, user_file_path)
                global in_game
                in_game = True
                try:
                    #room_serv_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    #room_serv_s.bind(room_addr)
                    #room_serv_s.listen(1)
                    #print(f"Room server strated at {room_addr}, waiting for player to connect...")
                    #room_client_s, room_client_addr = room_serv_s.accept()
                    #print(f"Player connected from {room_client_addr}")
                    role = "server"
                    ip = room_addr[0]
                    port = room_addr[1]
                    process = subprocess.Popen(["python", user_file_path, role, ip, str(port)],)
                    process.wait()
                    # start running script, download script , remember to break 
                except (ConnectionResetError, socket.error):
                    print("Error: Lost connection to the server while setting up the game server.")
                except Exception as e:
                    print(f"Unexpected error in game server: {e}")
                finally:
                    in_game = False
                    break                        
    elif role == "not-host":
        print("not host")
        while True:
            response = client_s.recv(1024).decode('utf-8')
            if response == "strt-err-sts":
                print("Game not started by host yet.")
                break
            elif response == "strt-ply-addr":
                client_s.send(b"addr")
                room_addr = client_s.recv(1024).decode('utf-8')
                room_addr = ast.literal_eval(room_addr)
                print(f"recv: {room_addr}")
                client_s.send(b"game")
                gamename = client_s.recv(1024).decode('utf-8')
                print(gamename)
                game_file_path = os.path.join("game_files", gamename)
                user_file_path = os.path.join("user", username, "games", gamename)
                shutil.copy(game_file_path, user_file_path)
                in_game = True
                try:
                    #room_client_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    #room_client_s.connect(room_addr)
                    role = "client"
                    ip = room_addr[0]
                    port = room_addr[1]
                    process = subprocess.Popen(["python", user_file_path, role, ip, str(port)],)
                    process.wait()
                except (ConnectionResetError, socket.error):
                    print("Error: Lost connection to the server while setting up the game server.")
                except Exception as e:
                    print(f"Unexpected error in game server: {e}")
                finally:
                    in_game = False
                    break
            else:
                print("error, start game")
                
def change_game(client_s, room_id):
    while True:
        command = input("\n---CHANGE GAME---\n(1) list available games\n(2) change game\n(3) back to room\nPlease enter command [1/2/3]: ")
        if command == "1":
            list_games(client_s)
        elif command == "2":
            client_s.send(b"change-game")
            client_s.send(room_id.encode('utf-8'))
            while True:
                response = client_s.recv(1024).decode('utf-8')
                if response == "chg-err":
                    print("Error: only hosts can change the game.")
                    break
                elif response == "chg-g":
                    while True:
                        gamename = input("Enter game name or press h to list games: ")
                        if gamename == "l":
                            list_games(client_s)
                            continue
                        else:
                            client_s.send(f"{gamename}".encode('utf-8'))
                            response = client_s.recv(1024).decode('utf-8')
                            if response == "chg-err-g":
                                print("Game not available.")
                                continue
                            elif response == "chg-ok":
                                print(f"Game changed to {gamename}.")
                                break
        elif command == "3":
            break
        else:
            print("Invalid command.")

def is_port_available(ip_port):
    ip, port = ip_port.split(":")
    port = int(port)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        result = sock.connect_ex((ip, port))
        return result != 0 

def find_available_port(ip="127.0.0.1", start_port=11117, end_port=16007):
    for port in range(start_port, end_port + 1):
        if is_port_available(f"{ip}:{port}"):
            return f"{port}"
    return None


# ---------invitation management------------
def invitation_management(client_s):
    """
    (1) list all request
    (2) accept request
    (3) back to lobby
    """
    while True:
        command = input("\n---INVITATION MANAGEMENT---\n(1) list invitations\n(2) join room\n(3) back to lobby\nPlease enter command [1/2/3]: ")
        if command == "1":
            client_s.send(b"list-invitation")
            print(client_s.recv(1024).decode('utf-8'))
        elif command == "2":
            join_prv_room(client_s)
        elif command == "3":
            break
        else:
            print("Invalid command.")
            
def join_prv_room(client_s):
    while True:
        command = input("\n-----JOIN ROOM-----\n(1) join room\n(2) back\nPlease enter command [1/2]: ")
        if command == "1":
            client_s.send(b"join-prv")
            room_id = input("Please enter room id: ")
            client_s.send(room_id.encode('utf-8'))
            while True:
                response = client_s.recv(1024).decode('utf-8')
                if response == "jn-prv-err-id":
                    print("Room closed.")
                    break
                elif response == "jn-prv-err-full":
                    print(f"{room_id} full.")
                    break
                elif response == "jn-prv-ok":
                    in_room(client_s, room_id)
                    break
        elif command == "2":
            break

# ------------join room---------------------
def join_pub_room(client_s):
    while True:
        command = input("\n-----JOIN ROOM-----\n(1) list rooms\n(2) join room\n(3) back to lobby\nPlease enter command [1/2/3]: ")
        if command == "1":
            print("Available rooms:")
            list_rooms(client_s) 
        elif command == "2":
            client_s.send(b"join-pub")
            room_id = input("Please enter room id: ")
            client_s.send(room_id.encode('utf-8'))
            while True:
                response = client_s.recv(1024).decode('utf-8')
                if response == "jn-pub-err-id":
                    print("Room closed.")
                    break
                elif response == "jn-pub-err-full":
                    print(f"{room_id} full.")
                    break
                elif response == "jn-pub-err-type":
                    print(f"{room_id} is not public.")
                    break
                elif response == "jn-pub-ok":
                    in_room(client_s, room_id)
                    break
        elif command == "3":
            break
            
            
# --------game development management--------
def game_dev_management(client_s):
    """
    (1) list my games
    (2) publish my game
    (3) update my game
    (4) back to room
    """
    while True:
        command = input("\n---GAME DEV MANAGEMENT---\n(1) list my games\n(2) publish my game\n(3) update my game\n(4) back to lobby\nPlease enter command [1/2/3/4]: ")
        if command == "1":
            list_my_games(client_s)
        elif command == "2":
            publish_game(client_s, username)
        elif command == "3":
            update_game(client_s, username)
        elif command == "4":
            break
        else:
            print("Invalid command.")
            
def list_my_games(client_s): # published games
    client_s.send(b"list-my-games")
    print(client_s.recv(1024).decode('utf-8'))
    return

def publish_game(client_s, username):
    user_dir = os.path.join("user", username, "my_games")
    files = os.listdir(user_dir)
    if not files:
        print("No files available.")
        return
    print("Available files:")
    for idx, file in enumerate(files, start=1):
        print(f"{idx}. {file}")
    try:
        choice = int(input("Enter the number of the file you want to publish: ")) - 1
        if choice < 0 or choice >= len(files):
            print("Invalid choice.")
            return
        filename = files[choice]
    except ValueError:
        print("Invalid input.")
        return
    client_s.send(b"publish-game")
    client_s.send(filename.encode('utf-8'))
    response = client_s.recv(1024).decode('utf-8')
    if response == "pub-err-file":
        print("Error: file doesnt exist")
    elif response == "pub-ok":
        print("Game published.")
    else:
        print(f"Error at pub game: {response}")
     
def update_game(client_s, username):
    user_dir = os.path.join("user", username, "my_games")
    files = os.listdir(user_dir)
    if not files:
        print("No files available.")
        return
    print("Available files:")
    for idx, file in enumerate(files, start=1):
        print(f"{idx}. {file}")
    try:
        choice = int(input("Enter the number of the file you want to publish: ")) - 1
        if choice < 0 or choice >= len(files):
            print("Invalid choice.")
            return
        filename = files[choice]
    except ValueError:
        print("Invalid input.")
        return
    client_s.send(b"update-game")
    client_s.send(filename.encode('utf-8'))
    response = client_s.recv(1024).decode('utf-8')
    if response == "up-err-file":
        print("Error: file doesnt exist")
    elif response == "up-err-owner":
        print(f"Error: not owner of {filename}")
    elif response == "up-ok":
        print("Game updated.")
    else:
        print(f"Error at update game: {response}")


# ------------logout-------------------
def logout(client_s):
    try:
        client_s.send(b"logout")
        response = client_s.recv(1024).decode('utf-8')
        if response == "out-ok":
            print("Logged out. Redirecting to log in page...")
            invitation_table.clear()
            in_game = False
            return True
    except (ConnectionResetError, socket.error):
        print("Connection to the server was lost during logout.")
        return False

# ------------list players------------------
def list_players(client_s):
    client_s.send(b"list-players")
    print(client_s.recv(1024).decode('utf-8'))
    return

# -------------list games--------------------
def list_games(client_s):
    client_s.send(b"list-games")
    print(f"{client_s.recv(1024).decode('utf-8')}")
    return

# ------------list rooms--------------------
def list_rooms(client_s):
    client_s.send(b"list-rooms")
    print(f"{client_s.recv(1024).decode('utf-8')}")
    return



if __name__ == "__main__":
    start()
