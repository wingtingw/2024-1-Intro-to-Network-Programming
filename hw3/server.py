# server.py

import socket
import threading
import os
import csv
import time
import shutil

room_data = {}
user_socket = {}
# -----------------helper functions-----------------
USER_FILE = "user_file.csv"
GAME_FILE = "game_file.csv"

def new_user_file():
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["username", "password", "status", "invitation"]) 

def new_game_file():
    if not os.path.exists(GAME_FILE):
        with open(GAME_FILE, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["game_name", "game_path", "publisher"]) 

def new_user_data(username, password, status="offline", invitation="null"):
    with open(USER_FILE, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([username, password, status, invitation])

def new_user_status(username, status):
    rows = []
    updated = False
    with open(USER_FILE, 'r') as file:
        reader = csv.reader(file)
        rows = list(reader)
    with open(USER_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        for row in rows:
            if row[0] == username:
                row[2] = status
                updated = True
            writer.writerow(row)
    return updated

def new_user_invitation(username, room_id):
    rows = []
    updated = False
    with open(USER_FILE, 'r') as file:
        reader = csv.reader(file)
        rows = list(reader)
    with open(USER_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        for row in rows:
            if row[0] == username:
                if row[3].strip().lower() == "null" or not row[3].strip():
                    row[3] = room_id
                else:
                    row[3] = f"{row[3]},{room_id}"
                updated = True
            writer.writerow(row)
    return updated

def user_exists(username):
    with open(USER_FILE, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row and row[0] == username:
                return True
    return False

def user_password(username, password):
    with open(USER_FILE, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row and row[0] == username and row[1] == password:
                return True
    return False

def user_status(username, status):
    with open(USER_FILE, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row and row[0] == username and row[2] == status:
                return True
    return False

def game_owner(username, game_name):
    with open(GAME_FILE, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row and row[0] == game_name and row[2] == username:
                return True
    return False

# -----------------server start----------------------
def start():
    server_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    new_user_file()
    new_game_file()
    port = 10007
    pmax = 11117
    while port <= pmax:
        try:
            print(f"Starting server on port {port}...")
            server_s.bind(('140.113.235.151', port))
            break
        except OSError:
            print(f"Port {port} is taken, trying {port + 1}...")
            port += 1
    server_s.listen(10)
    print(f"Server started on port {port}.")
    while True:
        client_s, client_addr = server_s.accept()
        print(f"Connection from {client_addr}")
        threading.Thread(target=handle_client, args=(client_s,client_addr,)).start()
        
def handle_client(client_s, client_addr):
    username = None
    while True:
        command = client_s.recv(1024).decode('utf-8')
        if command == "register":
            handle_register(client_s)
        elif command == "login":
            username = handle_login(client_s, client_addr)
        elif command == "logout":
            handle_logout(client_s, username)
        # ----create room-----
        elif command == "create":
            handle_create(client_s, client_addr, username)
        elif command == "list-players":
            list_players(client_s)
        elif command == "list-games":
            list_games(client_s)
        elif command == "invite":
            handle_invite(client_s, username)
        elif command == "start-game":
            handle_start_game(client_s, username)
        elif command == "change-game":
            handle_change_game(client_s, username)
        elif command == "leave":
            handle_leave(client_s, username)
        # ------game dev------
        elif command == "list-my-games":
            list_user_games(client_s, username)
        elif command == "publish-game":
            handle_game_publish(client_s, username)
        elif command == "update-game":
            handle_game_update(client_s, username)
        # -----join room------
        elif command == "join-pub":
            handle_join_pub(client_s, username)
        elif command == "list-rooms":
            list_rooms(client_s)
        # -----invitations-----
        elif command == "list-invitation":
            list_invitation(client_s, username)
        elif command == "join-prv":
            handle_join_prv(client_s, username)
  
def broadcast_message(message):
    for username, client_s in user_socket.items():
        try:
            client_s.send(message.encode('utf-8'))
        except Exception as e:
            print(f"Error broadcasting to {username}: {e}")
                
# -------------------register------------------------
def handle_register(client_s):
    client_s.send(b"reg-usr")
    username = client_s.recv(1024).decode('utf-8')
    if user_exists(username):
        client_s.send(b"reg-err")
    else:
        client_s.send(b"reg-psw")
        password = client_s.recv(1024).decode('utf-8')
        new_user_data(username, password)
        base_dir = "user"
        user_dir = os.path.join(base_dir, username)
        os.makedirs(user_dir, exist_ok=True)
        my_games_dir = os.path.join(user_dir, "my_games")
        games_dir = os.path.join(user_dir, "games")
        os.makedirs(my_games_dir, exist_ok=True)
        os.makedirs(games_dir, exist_ok=True)
        print(f"Directory created: {user_dir}, {my_games_dir}, {games_dir}")
        time.sleep(3)
        client_s.send(b"reg-ok")
    return

# --------------------login--------------------------
def handle_login(client_s, client_addr):
    client_s.send(b"in-usr")
    username = client_s.recv(1024).decode('utf-8')
    if not user_exists(username):
        client_s.send(b"in-err-usr")
        return None
    else:
        client_s.send(b"in-psw")
        password = client_s.recv(1024).decode('utf-8')
        if not user_password(username, password):
            client_s.send(b"in-err-psw")
            return None
        else:
            user_socket[username] = client_s
            new_user_status(username, "idle")
            client_s.send(b"in-ok")
            client_s.send(f"Logged in as {username}.".encode('utf-8'))
            broadcast_message(f"\nUser {username} joined the server.")
            return username
            
# --------------------logout-------------------------
def handle_logout(client_s, username):
    if username in user_socket:
        del user_socket[username]
    new_user_status(username, "offline")
    client_s.send(b"out-ok")
    broadcast_message(f"\nUser {username} left the server.")

# --------------------create-------------------------
def handle_create(client_s, client_addr, username):
    room_type = client_s.recv(1024).decode('utf-8') # 1 = public, 2 = private
    while True:
        ### game_data
        gamename = client_s.recv(1024).decode('utf-8')
        game_path = os.path.join("game_files", gamename)
        if not os.path.exists(game_path):
            client_s.send(b"cre-err-g")
            continue
        else:
            room_id = f"room_{len(room_data) + 1}"
            room_data[room_id] = {"host": username, "addr": "null", "participant": "null", "status": "waiting", "type": room_type, "game": gamename}
            new_user_status(username, "in room")
            client_s.send(b"cre-ok")
            client_s.send(room_id.encode('utf-8'))
            break
    
def handle_invite(client_s, username):  
    command = client_s.recv(1024).decode('utf-8')
    if command == "inv-usr":
        invitee = client_s.recv(1024).decode('utf-8')
        if not user_status(invitee, "idle"):
            client_s.send(b"inv-err-usr")
        else:
            client_s.send(b"inv-id")
            room_id = client_s.recv(1024).decode('utf-8')
            invitee_socket = user_socket.get(invitee, None)
            invitee_socket.send(f"Invitation: {room_id}".encode('utf-8'))
            new_user_invitation(invitee, room_id)
            client_s.send(b"inv-ok")
  
def handle_start_game(client_s, username):
    client_s.send(f"{username}".encode('utf-8'))
    room_id = client_s.recv(1024).decode('utf-8')
    if room_data[room_id]["host"] == username:
        client_s.send(b"host")
        if room_data[room_id]["participant"] == "null":
            client_s.send(b"strt-err-ppl")
            return
        room_data[room_id]["status"] = "started"
        new_user_status(username, "in game")
        client_s.send(b"strt-addr")
        room_addr = client_s.recv(1024).decode('utf-8')
        room_data[room_id]["addr"] = room_addr   
        # download game script   
        client_s.send(b"strt-ok")
        client_s.send(room_data[room_id]["game"].encode('utf-8'))
    elif room_data[room_id]["participant"] == username:
        client_s.send(b"not-host")
        if not room_data[room_id]["status"] == "started":
            client_s.send(b"strt-err-sts")
        else:
            new_user_status(username, "in game")
            client_s.send(b"strt-ply-addr")
            while True:
                command = client_s.recv(1024).decode('utf-8')
                if command == "addr":
                    client_s.send(f"{room_data[room_id]['addr']}".encode('utf-8'))
                elif command == "game":
                    client_s.send(f"{room_data[room_id]['game']}".encode('utf-8'))
         
def handle_change_game(client_s, username):
    room_id = client_s.recv(1024).decode('utf-8')
    if not room_data[room_id]["host"] == username:
        client_s.send(b"chg-err")
    else:
        client_s.send(b"chg-g")
        gamename = client_s.recv(1024).decode('utf-8')
        game_path = os.path.join("game_files", gamename)
        if not os.path.exists(game_path):
            client_s.send(b"chg-err-g")
        else:
            room_data[room_id]["game"] = gamename 
            client_s.send(b"chg-ok")

def list_players(client_s):
    player_list = []
    with open(USER_FILE, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row and row[2] == "idle":
                player_list.append(", ".join(row))
    if not player_list:
        client_s.send(b"No idle players found.")
    else:
        idle_players = "\n".join(player_list)
        client_s.send(idle_players.encode('utf-8'))
    return
             
def list_games(client_s):
    game_list = []
    with open(GAME_FILE, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
                game_list.append(", ".join(row))
    if not game_list:
        client_s.send(b"No games found.")
    else:
        game = "\n".join(game_list)
        client_s.send(game.encode('utf-8'))
    return

def handle_leave(client_s, username):
    room_id = client_s.recv(1024).decode('utf-8')
    if room_data[room_id]["host"] == username:
        if room_data[room_id]["participant"] == "null":
            del room_data[room_id]
            client_s.send(b"lv-ok")
        else:
            room_data[room_id]["host"] = room_data[room_id]["participant"]
            room_data[room_id]["participant"] = "null"
            client_s.send(b"lv-ok")
    else:
        room_data[room_id]["participant"] = "null"
        client_s.send(b"lv-ok")

# --------------------game dev-----------------------
def list_user_games(client_s, username):
    user_game_list = []
    with open(GAME_FILE, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row and row[2] == username:
                user_game_list.append(", ".join(row))
    if not user_game_list:
        client_s.send(b"No games found.")
    else:
        user_games = "\n".join(user_game_list)
        client_s.send(user_games.encode('utf-8'))
    return
    
def handle_game_publish(client_s, username):
    filename = client_s.recv(1024).decode('utf-8')
    user_file_path = os.path.join("user", username, "my_games", filename)  # Path to user's file
    game_file_path = os.path.join("game_files", filename) 
    if not os.path.exists(user_file_path):
        client_s.send(b"pub-err-file")
    else:
        shutil.copy(user_file_path, game_file_path)
        with open(GAME_FILE, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([filename, game_file_path, username])
        client_s.send(b"pub-ok")
    
def handle_game_update(client_s, username):
    filename = client_s.recv(1024).decode('utf-8')
    user_file_path = os.path.join("user", username, "my_games", filename)  # Path to user's file
    game_file_path = os.path.join("game_files", filename) 
    if not os.path.exists(user_file_path):
        client_s.send(b"up-err-file")
    elif not game_owner(username, filename):
        client_s.send(b"up-err-owner")
    else:
        shutil.copy(user_file_path, game_file_path)
        client_s.send(b"up-ok")

# ------------------invitation-----------------------
def list_invitation(client_s, username):
    try:
        with open(USER_FILE, 'r') as file:
            reader = csv.reader(file)
            header = next(reader)
            for row in reader:
                if row[0] == username: 
                    inv = row[3] if row[3] and row[3].strip() != "null" else "No invitations"
                    client_s.send(inv.encode('utf-8'))
                    return
    except Exception as e:
        client_s.send(f"Error: {str(e)}".encode('utf-8'))

def handle_join_prv(client_s, username):
    # check roomid, room full, change status
    room_id = client_s.recv(1024).decode('utf-8')
    if room_id not in room_data:
        client_s.send(b"jn-prv-err-id")
        return
    if not room_data[room_id]["participant"] == "null":
        client_s.send(b"jn-prv-err-full")
        return
    else:
        room_data[room_id]["participant"] = username
        new_user_status(username, "in room")
        client_s.send(b"jn-prv-ok")   
        return

# --------------------join---------------------------
def handle_join_pub(client_s, username):
    # update room data people
    room_id = client_s.recv(1024).decode('utf-8')
    if room_id not in room_data:
        client_s.send("jn-pub-err-id")
    if not room_data[room_id]["participant"] == "null":
        client_s.send(b"jn-pub-err-full")
        return
    # room participant == null, type = public
    elif not room_data[room_id]["type"] == "1":
        client_s.send(b"jn-pub-err-type")
        return
    else:
        room_data[room_id]["participant"] = username
        new_user_status(username, "in room")
        client_s.send(b"jn-pub-ok")
        return
           
def list_rooms(client_s):
    if not room_data:
        client_s.send(b"No rooms found.")
    else:
        room_list = []
        for room_id, room_info in room_data.items():
            room_details = f"Room ID: {room_id}, Host: {room_info['host']}, Address: {room_info['addr']}, " \
                           f"Status: {room_info['status']}, Type: {room_info['type']}, Game: {room_info['game']}"
            room_list.append(room_details)
        rooms = "\n".join(room_list)
        client_s.send(rooms.encode('utf-8'))
    return

if __name__ == "__main__":
    start()
