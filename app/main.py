import socket
import threading
import argparse
import os.path


def handle_file_get_request(file_name: str) -> bytes:
    try:
        file_path = os.path.join(files_directory, file_name)
        with open(file_path, "rb") as file:
            content = file.read()
            return format_response(200, "application/octet-stream", content)
    except FileNotFoundError:
        return not_found_response()


def handle_file_post_request(file_name: str, file_content: bytes) -> bytes:
    file_path = os.path.join(files_directory, file_name)
    response = b""
    try:
        with open(file_path, "wb") as file:
            file.write(file_content)
            response = format_response(201, "text/plain", b"")
    except:
        response = server_error_response()

    return response


def server_error_response() -> bytes:
    return b"HTTP/1.1 500 Internal Server Error\r\n\r\n"


def format_response(status_code: int, content_type: str, content: bytes) -> bytes:
    response = f"HTTP/1.1 {status_code}\r\n"
    response += f"Content-Type: {content_type}\r\n"
    response += f"Content-Length: {len(content)}\r\n\r\n"
    response = response.encode() + content
    print(response)
    return response


def not_found_response() -> bytes:
    return b"HTTP/1.1 404 Not Found\r\n\r\n"


def handle_request(client_socket) -> None:
    request = client_socket.recv(1024)
    lines = request.split(b"\r\n")

    http_method, http_path, http_version = lines[0].split(b" ")[0:3]

    http_host = ""
    http_user_agent = ""

    for line in lines:
        if line.startswith(b"Host:"):
            http_host = line.split(b" ")[1]
        if line.startswith(b"User-Agent:"):
            http_user_agent = line.split(b" ")[1]

    print(f"Method: {http_method}")
    print(f"Path: {http_path}")
    print(f"Version: {http_version}")

    if http_path == b"/":
        response = b"HTTP/1.1 200 OK\r\n\r\n"

    elif http_path.startswith(b"/echo/"):
        message = http_path.split(b"/echo/")[1]
        response = format_response(200, "text/plain", message)

    elif http_path == b"/user-agent":
        response = format_response(200, "text/plain", http_user_agent)

    elif http_path.startswith(b"/files/") and http_method == b"GET":
        file_name = http_path.split(b"/files/")[1]
        response = handle_file_get_request(str(file_name.decode()))

    elif http_path.startswith(b"/files/") and http_method == b"POST":
        file_name = http_path.split(b"/files/")[1]
        file_content = lines[-1]
        response = handle_file_post_request(
            str(file_name.decode()), file_content)

    else:
        response = not_found_response()

    client_socket.sendall(response)
    client_socket.close()


def main():
    server_socket = socket.create_server(("localhost", 4221))

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        parser = argparse.ArgumentParser()
        parser.add_argument("--directory", type=str)
        args = parser.parse_args()
        global files_directory
        files_directory = args.directory
        threading.Thread(target=handle_request, args=(client_socket,)).start()


if __name__ == "__main__":
    main()
