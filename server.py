import socket
import sqlite3
import zlib
import random

def generate_hash(s):
    return zlib.crc32(s.encode())

def generate_ticket():
    con = sqlite3.connect("ticketInfo")
    cur = con.cursor()
    while True:
        name = input("Enter Name : ")
        age = int(input("Enter Age : "))
        train = int(input("Enter Train No : "))
        coach = int(input("Enter Coach : "))
        seat = int(input("Enter Seat : "))
        r = random.randint(10000, 99999)
        used = 0
        hval = generate_hash(name + str(age) + str(train) + str(coach) + str(seat) + str(r))
        try:
            temp = cur.execute("SELECT EXISTS(SELECT 1 FROM tickets WHERE name = ? AND age = ? AND trainNo = ? AND coach = ? AND seat = ? )",(name,age,train,coach,seat,)).fetchone()[0]
            if temp == 1:
                raise ValueError('A very specific bad thing happened.')
            cur.execute("INSERT INTO tickets VALUES (? , ? , ? , ? , ? , ? , ? , ?)", (hval,name,age,train,coach,seat,r,used,))
            res = cur.execute("SELECT * FROM tickets WHERE hval = ?",(hval,))
            con.commit()
            print(res.fetchall())
        except:
            print("Error Occured")
            break
    con.close()

def start_server(host='0.0.0.0', port=65432):
    # Connecting to Database
    con = sqlite3.connect("ticketInfo")
    cur = con.cursor()

    # Binding socket addresses and port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        # Starts listening if any device want to connect
        server_socket.listen()
        print("Server is listening on", host, ":", port)

        while True:
            # This line will only end 
            client_socket, client_address = server_socket.accept()
            with client_socket:
                print("Connected to:", client_address)
                
                while True:
                    try:
                        # Receive data from client
                        data = client_socket.recv(1024)
                        if not data:
                            print("Client disconnected.")
                            break

                        number = int(data.decode())
                        print("Received from client:", number)

                        # Check if ticket is used or available
                        exists = cur.execute("SELECT EXISTS(SELECT 1 FROM tickets WHERE hval = ?)",(number,)).fetchone()[0]
                        if exists == 0:
                            client_socket.sendall("False : Ticket don't exists".encode())
                        else:
                            try:
                                used = cur.execute("SELECT used FROM tickets WHERE hval = ?",(number,)).fetchone()[0]
                                if int(used) == 2:
                                    cur.execute("DELETE FROM tickets WHERE hval = ?",(number,))
                                    con.commit()
                                    client_socket.sendall("False : Ticket already used".encode())
                                else:
                                    cur.execute("UPDATE tickets SET used = ? WHERE hval = ?",(int(used)+1,number,))
                                    con.commit()
                                    client_socket.sendall("True".encode())
                            except:
                                client_socket.sendall("False : Error in DB".encode())

                    except ValueError:
                        print("Invalid data received. Expected an integer.")
                    except ConnectionResetError:
                        print("Client unexpectedly disconnected.")
                        break
                break
    con.close()

if __name__ == "__main__":
    start_server()

