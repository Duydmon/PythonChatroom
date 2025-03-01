import hashlib
import socket
import ssl
import threading

HOST = "127.0.0.1"
PORT = 25219
CERT_FILE = "/home/duyd/PycharmProjects/XacThucClient/secure/server.crt"  # Chứng chỉ CA dùng để xác thực server

def receive_messages(ssl_client):
    while True:
        try:
            message = ssl_client.recv(1024).decode()
            if not message:
                break
            print(message)
        except:
            break


def connect_to_server():
    # Tạo socket TCP
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Tạo SSL context để xác thực chứng chỉ server
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    context.load_verify_locations(CERT_FILE)  # Load chứng chỉ để xác thực server

    # Kết nối an toàn đến server
    ssl_client = context.wrap_socket(client, server_hostname=HOST)
    ssl_client.connect((HOST, PORT))

    # Nhận menu từ server
    print(ssl_client.recv(1024).decode(), end="")
    choice = input()
    ssl_client.send(choice.encode())
    while True:
        #print(ssl_client.recv(1024).decode(), end='')
        if choice == "1":  # Đăng nhập
            for _ in range(3):
                print(ssl_client.recv(1024).decode(), end="")
                username = input()
                ssl_client.send(username.encode())

                print(ssl_client.recv(1024).decode(), end="")
                password = input()
                hashpass = hashlib.sha256(password.encode()).hexdigest()  # Hash mật khẩu
                ssl_client.send(hashpass.encode())

                response = ssl_client.recv(1024).decode()
                print(f"Server: {response}")

                if "Đăng nhập thành công" in response:
                    threading.Thread(target=receive_messages, args=(ssl_client,)).start()
                    while True:
                        message = input()
                        ssl_client.send(message.encode())
                        if message.lower() == "exit":
                            break

                elif "Hết số lần thử" in response:
                    print("Bạn đã hết số lần thử, kết nối bị ngắt.")
                    break

        elif choice == "2":  # Đăng ký
            while True:
                print(ssl_client.recv(1024).decode(), end="")
                username = input()
                ssl_client.send(username.encode())

                response = ssl_client.recv(1024).decode()
                print(f"Server: {response}")
                if "Username đã tồn tại" in response:
                    continue  # Nhập lại username nếu đã tồn tại

                print(ssl_client.recv(1024).decode(), end="")
                password = input()
                hashpass = hashlib.sha256(password.encode()).hexdigest()
                ssl_client.send(hashpass.encode())

                print(ssl_client.recv(1024).decode(), end="")
                confirm_password = input()
                hashpass_confirm = hashlib.sha256(confirm_password.encode()).hexdigest()
                ssl_client.send(hashpass_confirm.encode())

                response = ssl_client.recv(1024).decode()
                print(f"Server: {response}")

                if "Đăng ký thành công" in response:
                    continue

    # Đóng kết nối sau khi hoàn thành
    ssl_client.close()

if __name__ == "__main__":
    connect_to_server()
