import hashlib
import sqlite3
import random
import socket
import ssl
import threading

HOST = "127.0.0.1"
PORT = 25219
CERT_FILE = "/home/duyd/PycharmProjects/XacThucClient/secure/server.crt"
KEY_FILE = '/home/duyd/PycharmProjects/XacThucClient/secure/server.key'

clients = []  # Danh sách các kết nối client



# Kết nối đến SQLite Database
def connect_db():
    conn = sqlite3.connect("/home/duyd/Sqlite/Test.db")
    cursor = conn.cursor()
    return conn, cursor


# Hàm xác thực đăng nhập
def authenticate(username, password):
    conn, cursor = connect_db()
    cursor.execute("SELECT Salt FROM Client WHERE Username=?", (username,))
    result = cursor.fetchone()

    if result is None:
        conn.close()
        return False  # Username không tồn tại

    salt = result[0]
    realhash = hashlib.sha256((salt + password).encode()).hexdigest()
    cursor.execute("SELECT * FROM Client WHERE Username=? AND Password=?", (username, realhash))
    result = cursor.fetchone()
    conn.close()

    return result is not None  # Trả về True nếu đăng nhập thành công


# Kiểm tra xem Username có tồn tại không
def username_exists(username):
    conn, cursor = connect_db()
    cursor.execute("SELECT * FROM Client WHERE Username=?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


# Thêm user mới vào database
def register_user(username, password, salt):
    conn, cursor = connect_db()
    cursor.execute("INSERT INTO Client (Username, Password, Salt) VALUES (?, ?, ?)",
                   (username, password, salt))
    conn.commit()
    conn.close()

#chatroom
def handle_chat(ssl_client, username):
    ssl_client.send("Bạn đã vào chat room! Nhập 'exit' để thoát.\n".encode())

    while True:
        try:
            message = ssl_client.recv(1024).decode().strip()
            if message.lower() == "exit":
                ssl_client.send("Bạn đã thoát khỏi chat room.\n".encode())
                clients.remove(ssl_client)
                break

            broadcast(f"{username}: {message}", ssl_client)
        except:
            clients.remove(ssl_client)
            break


# Gửi tin nhắn đến tất cả client trong chat room
def broadcast(message, sender):
    for client in clients:
        if client != sender:
            try:
                client.send((message + "\n").encode())
            except:
                clients.remove(client)


# Xử lý đăng nhập
def handle_login(ssl_client):
    try:
        attempts = 3
        while attempts > 0:
            ssl_client.send("Nhập Username: ".encode())
            username = ssl_client.recv(1024).decode().strip()

            ssl_client.send("Nhập Password: ".encode())
            password = ssl_client.recv(1024).decode().strip()

            if authenticate(username, password):
                ssl_client.send("Đăng nhập thành công! Bạn sẽ vào chat room.\n".encode())
                clients.append(ssl_client)
                handle_chat(ssl_client, username)
                return
            else:
                attempts -= 1
                if attempts > 0:
                    ssl_client.send(f"Đăng nhập thất bại! Bạn còn {attempts} lần thử.".encode())
                else:
                    ssl_client.send("Đăng nhập thất bại! Hết số lần thử. Kết nối bị ngắt.".encode())
                    break
    except ConnectionResetError:
        print("[*] Client đóng kết nối đột ngột!")
    finally:
        ssl_client.close()


# Xử lý đăng ký
def handle_register(ssl_client):
    try:
        while True:
            ssl_client.send("Hãy nhập username mới: ".encode())
            username = ssl_client.recv(1024).decode().strip()

            if username_exists(username):
                ssl_client.send("Username đã tồn tại. Hãy thử lại.\n".encode())
                continue
            else:
                ssl_client.send("Username hợp lệ.\n".encode())

            ssl_client.send("Hãy nhập mật khẩu: ".encode())
            password = ssl_client.recv(1024).decode().strip()

            ssl_client.send("Hãy đánh lại mật khẩu: ".encode())
            confirm_password = ssl_client.recv(1024).decode().strip()

            if password != confirm_password:
                ssl_client.send("Xác nhận mật khẩu phải giống nhau. Hãy thử lại từ đầu.\n".encode())
                continue

            salt = str(random.randint(100000, 999999))
            passhash = hashlib.sha256((salt + password).encode()).hexdigest()

            register_user(username, passhash, salt)
            ssl_client.send("Đăng ký thành công! Bạn có thể đăng nhập ngay bây giờ.\n".encode())
            handle_client(ssl_client)
            return
    except ConnectionResetError:
        print("[*] Client đóng kết nối đột ngột!")


# Xử lý Client
def handle_client(ssl_client):
    try:
        ssl_client.send("Chọn một tùy chọn:\n1. Đăng nhập\n2. Đăng ký\nNhập lựa chọn: ".encode())
        choice = ssl_client.recv(1024).decode().strip()

        if choice == "1":
            handle_login(ssl_client)
        elif choice == "2":
            handle_register(ssl_client)
        else:
            ssl_client.send("Lựa chọn không hợp lệ.".encode())
    except ConnectionResetError:
        print("[*] Client đóng kết nối đột ngột!")
    finally:
        ssl_client.close()


# Khởi động Server với SSL
def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen(5)
        print(f"[*] Server đang lắng nghe trên {HOST}:{PORT}")

        # Thiết lập SSL
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)

        while True:
            client, addr = server.accept()
            ssl_client = context.wrap_socket(client, server_side=True)
            print(f"[*] Kết nối bảo mật từ {addr[0]}:{addr[1]}")
            threading.Thread(target=handle_client, args=(ssl_client,)).start()


if __name__ == "__main__":
    start_server()
