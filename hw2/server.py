# server.py

import socket
import threading
import time

user_data = {}
room_data = {}

def start():
    print("Starting game server on port 10007...")
    server_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = 10007
    pmax = 11117
    while port <= pmax:
        try:
            server_s.bind(('127.0.0.1', port))
            break
        except OSError:
            print(f"Port {port} is taken, trying {port + 1}...")
            port += 1
    server_s.listen(10)
    print(f"Server started on port {port}, waiting for connection...")
    
    while True:
        client_s, client_addr = server_s.accept()
        print(f"Connection from {client_addr}")
        threading.Thread(target=handle_client, args=(client_s,)).start()


def handle_client(client_s):
    username = None
    while True:
        command = client_s.recv(1024).decode('utf-8')  
        
        if username and user_data[username]["inviting"]:
            if command == "yes":
                print("Received acceptance for invitation")
                user_data[username]["inviting"] = False
                user_data[username]["accepted"] = True
                # print(f"{username}, {user_data[username]["accepted"]}")
            elif command == "no":
                print("Invitation rejected")
                user_data[username]["inviting"] = False
                user_data[username]["accepted"] = False
            else:
                client_s.send(b"Expected 'yes' or 'no' for invitation.")
            continue  # Skip to the next loop iteration
           
        if command == "register":
            username = handle_register(client_s)
        elif command == "login":
            username = handle_login(client_s)
        elif command == "logout":
            handle_logout(client_s, username)
            break
        elif command == "c":
            handle_create(client_s, username)
        elif command == "j":
            handle_join(client_s, username)
        elif command == "end":
            handle_end_game(username)
        elif command == "yes":
            user_data[username]["accepted"] = True
            print("wrong")
        else:
            client_s.send(b"Invalid command.")


def handle_register(client_s):
    client_s.send(b"u") # username
    username = client_s.recv(1024).decode('utf-8')
    if username in user_data:
        client_s.send(b"error")
    else:
        client_s.send(b"p") # password
        password = client_s.recv(1024).decode('utf-8')
        user_data[username] = {"password": password, "status": "offline", "socket": client_s, "inviting": False, "accepted": False}
        client_s.send(b"ok")
        print(password)
    return None


def handle_login(client_s):
    client_s.send(b"u") # username
    username = client_s.recv(1024).decode('utf-8')
    client_s.send(b"p") # password
    password = client_s.recv(1024).decode('utf-8')
    if username not in user_data:
        client_s.send(b"error-u")
        return None
    elif user_data[username]["password"] != password:
        client_s.send(b"error-p")
        print(user_data[username]["password"])
        return None
    elif user_data[username]["password"] == password:
        client_s.send(b"ok")
        user_data[username]["socket"] = client_s
        user_data[username]["status"] = "idle"
        user_status_list = "\n".join(f"{user}: {info['status']}" for user, info in user_data.items() if info['status'] != 'offline')
        available_rooms = [room_id for room_id, details in room_data.items() if details["status"] == "waiting" and details["type"] == "public"]
        if not available_rooms:
            available_rooms = ("No public rooms waiting for players.")
        client_s.send(f"Logged in as {username}. Welcome, {username}!\n\nCurrent users:\n{user_status_list}\n{available_rooms}".encode('utf-8'))
        return username
    else:
        return None


def handle_logout(client_s, username):
    if username in user_data:
        user_data[username]["status"] = "offline"
        client_s.send(b"ok")
    else:
        client_s.send(b"error")


def handle_create(client_s, username):
    if user_data[username]["status"] != "idle":
        client_s.send(b"error")
    else:
        client_s.send(b"ok")
    command = client_s.recv(1024).decode('utf-8')
    if command == "cpb": # create public
        handle_create_public(client_s, username)
    elif command == "cpv": # create private
        handle_create_private(client_s, username)


def handle_create_public(client_s, username):
    client_s.send(b"gt") # ask game type
    game_12 = client_s.recv(1024).decode('utf-8')
    client_s.send(b"p") # ask port
    ip, game_port = client_s.recv(1024).decode('utf-8').split(":")
    room_id = f"room_{len(room_data) + 1}"
    room_data[room_id] = {"host": username, "status": "waiting", "game_12": game_12, "type": "public", "ip": ip, "game_port": game_port}
    user_data[username]["status"] = "in room"
    client_s.send(b"ok")
    if client_s.recv(1024).decode('utf-8') == "end":
        user_data[username]["status"] = "idle"
        print(f"{username} : idle")


def handle_join(client_s, username):
    if user_data[username]["status"] != "idle":
        client_s.send(b"error")
        return
    else:
        client_s.send(b"ok")
    available_rooms = [room_id for room_id, details in room_data.items() if details["status"] == "waiting" and details["type"] == "public"]
    if available_rooms:
        client_s.send(f"Available rooms: {', '.join(available_rooms)}".encode('utf-8'))
        room_id = client_s.recv(1024).decode('utf-8')
        if room_id in available_rooms:
            room_data[room_id]["status"] = "in game"
            user_data[username]["status"] = "in game"
            client_s.send(f"ok:{room_data[room_id]['ip']}:{room_data[room_id]['game_port']}:{room_data[room_id]['game_12']}".encode('utf-8'))
    else:
        client_s.send(b"no")
    if client_s.recv(1024).decode('utf-8') == "end":
            user_data[username]["status"] = "idle"
            print(f"{username} : idleee")


def handle_create_private(client_s, username):
    client_s.send(b"gt")
    game_12 = client_s.recv(1024).decode('utf-8')
    room_id = f"room_{len(room_data) + 1}"
    room_data[room_id] = {"host": username, "status": "in room", "type": "private", "game_12": game_12}
    user_data[username]["status"] = "in room"
    client_s.send(b"cpvok")
    handle_invite(client_s, username, room_id)
  
  
def handle_invite(client_s, host_username, room_id):
    invite_response = client_s.recv(1024).decode('utf-8')
    if invite_response.startswith("inv"):
        invitee_username = invite_response.split()[1]
        if invitee_username in user_data and user_data[invitee_username]["status"] == "idle":
            client_s.send(b"i-ok")          
            user_data[invitee_username]["inviting"] = True
            invitee_socket = user_data[invitee_username]["socket"]
            invitee_socket.send(f"Invitation from {host_username}.".encode('utf-8')) 
            time.sleep(3)          
            # response = invitee_socket.recv(1024).decode('utf-8')
            # print(f"inviteeeee {user_data[invitee_username]["accepted"]}")
            if user_data[invitee_username]["accepted"] == True:
                # print("1ac")
                client_s.send(b"ac")
                # print("accept")
                ip_port = client_s.recv(1024).decode('utf-8')
                # print("recv ip port")
                invitee_socket.send(f"ok:{ip_port}:{room_data[room_id]['game_12']}".encode('utf-8'))
                # print("sent ip port")

                room_data[room_id]["status"] = "in game"
                user_data[host_username]["status"] = "in game"
                user_data[invitee_username]["status"] = "in game"
            else:
                client_s.send(b"invite_rejected")
                user_data[invitee_username]["status"] = "idle"
        else:
            client_s.send(b"error")  # Invitee not found or not idle


def handle_end_game(username):
    if username in user_data:
        user_data[username]["status"] = "idle"
        user_data[username]["accepted"] = False

        room_to_remove = None
        for room_id, details in room_data.items():
            if details["host"] == username:
                room_to_remove = room_id
                break
        
        if room_to_remove:
            del room_data[room_to_remove]
            print(f"Room {room_to_remove} removed. {username}'s status set to idle.")


if __name__ == "__main__":
    start()
