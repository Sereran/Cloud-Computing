import socket
import json

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#Allow port reuse
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_address = ('127.0.0.1', 8000)
server_socket.bind(server_address)

server_socket.listen(5)
print("listening on port 8000...")

while True:
    client_socket, client_address = server_socket.accept()

    try:
        request_data = client_socket.recv(4096).decode('utf-8')

        if not request_data:
            continue

        #Loop until we get the whole payload if the data is larger than 4096 bytes (or if the client is sending it in multiple TCP packets for any reason)
        if '\r\n\r\n' in request_data:
            headers_part, body = request_data.split('\r\n\r\n', 1)

            #Find the Content-Length header
            content_length = 0
            for line in headers_part.split('\r\n'):
                if line.lower().startswith('content-length:'):
                    content_length = int(line.split(':')[1].strip())

            while len(body.encode('utf-8')) < content_length:
                chunk = client_socket.recv(4096).decode('utf-8', errors='ignore')
                if not chunk:
                    break
                body += chunk

            #Reconstruct the full string
            request_data = headers_part + '\r\n\r\n' + body

        print("\n Received request:")
        print(request_data)

        #Parse the HTTP request line
        request_lines = request_data.split('\r\n')
        request_line = request_lines[0]
        method, path, version = request_line.split(' ')

        if method == 'OPTIONS':
            http_response = (
                "HTTP/1.1 204 No Content\r\n"
                "Access-Control-Allow-Origin: *\r\n"
                "Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS\r\n"
                "Access-Control-Allow-Headers: Content-Type\r\n"
                "Connection: close\r\n"
                "\r\n"
            )
            client_socket.sendall(http_response.encode('utf-8'))


        #GET REQUESTS

        elif method == 'GET' and path == '/games':
            db_path = 'database/games.json'
            try:
                with open(db_path, 'r', encoding='utf-8') as file:
                    games_db = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                games_db = []

            response_body = json.dumps(games_db)
            http_response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json\r\n"
                "Access-Control-Allow-Origin: *\r\n"
                f"Content-Length: {len(response_body)}\r\n"
                "Connection: close\r\n"
                "\r\n"
                f"{response_body}"
            )
            client_socket.sendall(http_response.encode('utf-8'))

        elif method == 'GET' and path.startswith('/games/') and len(path.strip('/').split('/')) == 2:
            try:
                game_id = int(path.strip('/').split('/')[-1])
            except ValueError:
                error_response = "HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n"
                client_socket.sendall(error_response.encode('utf-8'))
                continue

            db_path = 'database/games.json'
            try:
                with open(db_path, 'r', encoding='utf-8') as file:
                    games_db = json.load(file)

                found_game = None
                for game in games_db:
                    if game.get('id') == game_id:
                        found_game = game
                        break

                if found_game:
                    response_body = json.dumps(found_game)
                    http_response = (
                        "HTTP/1.1 200 OK\r\n"
                        "Content-Type: application/json\r\n"
                        "Access-Control-Allow-Origin: *\r\n"
                        f"Content-Length: {len(response_body)}\r\n"
                        "Connection: close\r\n"
                        "\r\n"
                        f"{response_body}"
                    )
                    client_socket.sendall(http_response.encode('utf-8'))
                else:
                    error_body = json.dumps({"error": f"Game with ID {game_id} not found"})
                    http_error = (
                        "HTTP/1.1 404 Not Found\r\n"
                        "Content-Type: application/json\r\n"
                        "Access-Control-Allow-Origin: *\r\n"
                        "\r\n"
                        f"{error_body}"
                    )
                    client_socket.sendall(http_error.encode('utf-8'))
            except (FileNotFoundError, json.JSONDecodeError):
                error_response = "HTTP/1.1 500 Internal Server Error\r\nConnection: close\r\n\r\n"
                client_socket.sendall(error_response.encode('utf-8'))


        #POST REQUESTS

        elif method == 'POST' and path == '/games':
            parts = request_data.split('\r\n\r\n', 1)
            if len(parts) > 1:
                body = parts[1]
                try:
                    new_game_data = json.loads(body)
                    db_path = 'database/games.json'

                    try:
                        with open(db_path, 'r', encoding='utf-8') as file:
                            games_db = json.load(file)
                    except (FileNotFoundError, json.JSONDecodeError):
                        games_db = []

                    if len(games_db) > 0:
                        highest_id = max(game.get('id', 0) for game in games_db)
                        new_game_data['id'] = highest_id + 1
                    else:
                        new_game_data['id'] = 1

                    games_db.append(new_game_data)

                    with open(db_path, 'w', encoding='utf-8') as file:
                        json.dump(games_db, file, indent=4)

                    response_body = json.dumps({"message": "Game saved successfully!"})
                    http_response = (
                        "HTTP/1.1 201 Created\r\n"
                        "Content-Type: application/json\r\n"
                        "Access-Control-Allow-Origin: *\r\n"
                        f"Content-Length: {len(response_body)}\r\n"
                        "Connection: close\r\n"
                        "\r\n"
                        f"{response_body}"
                    )
                    client_socket.sendall(http_response.encode('utf-8'))
                except json.JSONDecodeError:
                    error_response = "HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n"
                    client_socket.sendall(error_response.encode('utf-8'))

        elif method == 'POST' and path.startswith('/games/') and path.endswith('/tags') and len(path.strip('/').split('/')) == 3:
            try:
                game_id = int(path.strip('/').split('/')[1])
            except ValueError:
                error_response = "HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n"
                client_socket.sendall(error_response.encode('utf-8'))
                continue

            parts = request_data.split('\r\n\r\n', 1)
            if len(parts) > 1:
                body = parts[1]
                try:
                    tag_data = json.loads(body)
                    new_tag = tag_data.get('tag')

                    if not new_tag:
                        error_body = json.dumps({"error": "Missing 'tag' in request body."})
                        http_error = f"HTTP/1.1 400 Bad Request\r\nContent-Type: application/json\r\n\r\n{error_body}"
                        client_socket.sendall(http_error.encode('utf-8'))
                        continue

                    db_path = 'database/games.json'
                    try:
                        with open(db_path, 'r', encoding='utf-8') as file:
                            games_db = json.load(file)
                    except (FileNotFoundError, json.JSONDecodeError):
                        games_db = []

                    found_game = None
                    for game in games_db:
                        if game.get('id') == game_id:
                            if new_tag not in game['tags']:
                                game['tags'].append(new_tag)
                            found_game = game
                            break

                    if found_game:
                        with open(db_path, 'w', encoding='utf-8') as file:
                            json.dump(games_db, file, indent=4)

                        response_body = json.dumps({
                            "message": f"Tag '{new_tag}' successfully added.",
                            "updated_game": found_game
                        })
                        http_response = (
                            "HTTP/1.1 201 Created\r\n"
                            "Content-Type: application/json\r\n"
                            "Access-Control-Allow-Origin: *\r\n"
                            f"Content-Length: {len(response_body)}\r\n"
                            "Connection: close\r\n"
                            "\r\n"
                            f"{response_body}"
                        )
                        client_socket.sendall(http_response.encode('utf-8'))
                    else:
                        error_body = json.dumps({"error": f"Game with ID {game_id} not found."})
                        http_error = f"HTTP/1.1 404 Not Found\r\nContent-Type: application/json\r\n\r\n{error_body}"
                        client_socket.sendall(http_error.encode('utf-8'))
                except json.JSONDecodeError:
                    error_response = "HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n"
                    client_socket.sendall(error_response.encode('utf-8'))


        #PUT REQUESTS

        elif method == 'PUT' and path.startswith('/games/') and len(path.strip('/').split('/')) == 2:
            try:
                game_id = int(path.strip('/').split('/')[-1])
            except ValueError:
                error_response = "HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n"
                client_socket.sendall(error_response.encode('utf-8'))
                continue

            parts = request_data.split('\r\n\r\n', 1)
            if len(parts) > 1:
                body = parts[1]
                try:
                    updated_game_data = json.loads(body)
                    db_path = 'database/games.json'
                    try:
                        with open(db_path, 'r', encoding='utf-8') as file:
                            games_db = json.load(file)
                    except (FileNotFoundError, json.JSONDecodeError):
                        games_db = []

                    found_index = None
                    for index, game in enumerate(games_db):
                        if game.get('id') == game_id:
                            found_index = index
                            break

                    if found_index is not None:
                        #Replace the old game with the new one
                        games_db[found_index] = updated_game_data
                        games_db[found_index]['id'] = game_id

                        with open(db_path, 'w', encoding='utf-8') as file:
                            json.dump(games_db, file, indent=4)

                        response_body = json.dumps({
                            "message": f"Game {game_id} updated successfully.",
                            "game": games_db[found_index]
                        })
                        http_response = (
                            "HTTP/1.1 200 OK\r\n"
                            "Content-Type: application/json\r\n"
                            "Access-Control-Allow-Origin: *\r\n"
                            f"Content-Length: {len(response_body)}\r\n"
                            "Connection: close\r\n"
                            "\r\n"
                            f"{response_body}"
                        )
                        client_socket.sendall(http_response.encode('utf-8'))
                    else:
                        error_body = json.dumps({"error": f"Game with ID {game_id} not found."})
                        http_error = f"HTTP/1.1 404 Not Found\r\nContent-Type: application/json\r\n\r\n{error_body}"
                        client_socket.sendall(http_error.encode('utf-8'))
                except json.JSONDecodeError:
                    error_response = "HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n"
                    client_socket.sendall(error_response.encode('utf-8'))

        elif method == 'PUT' and path.startswith('/games/') and path.endswith('/tags') and len(path.strip('/').split('/')) == 3:
            try:
                game_id = int(path.strip('/').split('/')[1])
            except ValueError:
                error_response = "HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n"
                client_socket.sendall(error_response.encode('utf-8'))
                continue

            parts = request_data.split('\r\n\r\n', 1)
            if len(parts) > 1:
                body = parts[1]
                try:
                    tag_data = json.loads(body)

                    if 'tags' not in tag_data or not isinstance(tag_data['tags'], list):
                        error_body = json.dumps({"error": "Missing or invalid 'tags' array in request body."})
                        http_error = f"HTTP/1.1 400 Bad Request\r\nContent-Type: application/json\r\n\r\n{error_body}"
                        client_socket.sendall(http_error.encode('utf-8'))
                        continue

                    new_tags_array = tag_data['tags']
                    db_path = 'database/games.json'
                    try:
                        with open(db_path, 'r', encoding='utf-8') as file:
                            games_db = json.load(file)
                    except (FileNotFoundError, json.JSONDecodeError):
                        games_db = []

                    found_game = None
                    for game in games_db:
                        if game.get('id') == game_id:
                            game['tags'] = new_tags_array
                            found_game = game
                            break

                    if found_game:
                        with open(db_path, 'w', encoding='utf-8') as file:
                            json.dump(games_db, file, indent=4)

                        response_body = json.dumps({
                            "message": f"Tags for Game {game_id} completely replaced.",
                            "updated_game": found_game
                        })
                        http_response = (
                            "HTTP/1.1 200 OK\r\n"
                            "Content-Type: application/json\r\n"
                            "Access-Control-Allow-Origin: *\r\n"
                            f"Content-Length: {len(response_body)}\r\n"
                            "Connection: close\r\n"
                            "\r\n"
                            f"{response_body}"
                        )
                        client_socket.sendall(http_response.encode('utf-8'))
                    else:
                        error_body = json.dumps({"error": f"Game with ID {game_id} not found."})
                        http_error = f"HTTP/1.1 404 Not Found\r\nContent-Type: application/json\r\n\r\n{error_body}"
                        client_socket.sendall(http_error.encode('utf-8'))
                except json.JSONDecodeError:
                    error_response = "HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n"
                    client_socket.sendall(error_response.encode('utf-8'))


        #DELETE REQUESTS

        elif method == 'DELETE' and path == '/games':
            db_path = 'database/games.json'
            try:
                with open(db_path, 'w', encoding='utf-8') as file:
                    json.dump([], file)

                response_body = json.dumps({"message": "The entire game library has been cleared!"})
                http_response = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: application/json\r\n"
                    "Access-Control-Allow-Origin: *\r\n"
                    f"Content-Length: {len(response_body)}\r\n"
                    "Connection: close\r\n"
                    "\r\n"
                    f"{response_body}"
                )
                client_socket.sendall(http_response.encode('utf-8'))
            except IOError:
                error_response = "HTTP/1.1 500 Internal Server Error\r\nConnection: close\r\n\r\n"
                client_socket.sendall(error_response.encode('utf-8'))

        elif method == 'DELETE' and path.startswith('/games/') and len(path.strip('/').split('/')) == 2:
            try:
                game_id = int(path.strip('/').split('/')[-1])
            except ValueError:
                error_response = "HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n"
                client_socket.sendall(error_response.encode('utf-8'))
                continue

            db_path = 'database/games.json'
            try:
                with open(db_path, 'r', encoding='utf-8') as file:
                    games_db = json.load(file)

                initial_length = len(games_db)
                games_db = [game for game in games_db if game.get('id') != game_id]

                if len(games_db) < initial_length:
                    with open(db_path, 'w', encoding='utf-8') as file:
                        json.dump(games_db, file, indent=4)

                    response_body = json.dumps({"message": f"Game {game_id} deleted successfully."})
                    http_response = (
                        "HTTP/1.1 200 OK\r\n"
                        "Content-Type: application/json\r\n"
                        "Access-Control-Allow-Origin: *\r\n"
                        f"Content-Length: {len(response_body)}\r\n"
                        "Connection: close\r\n"
                        "\r\n"
                        f"{response_body}"
                    )
                    client_socket.sendall(http_response.encode('utf-8'))
                else:
                    error_body = json.dumps({"error": f"Game with ID {game_id} not found"})
                    http_error = (
                        "HTTP/1.1 404 Not Found\r\n"
                        "Content-Type: application/json\r\n"
                        "Access-Control-Allow-Origin: *\r\n"
                        "\r\n"
                        f"{error_body}"
                    )
                    client_socket.sendall(http_error.encode('utf-8'))
            except (FileNotFoundError, json.JSONDecodeError):
                error_response = "HTTP/1.1 500 Internal Server Error\r\nConnection: close\r\n\r\n"
                client_socket.sendall(error_response.encode('utf-8'))

        #Fallback for paths that don't match any route
        else:
            error_body = json.dumps({"error": "Endpoint not found"})
            http_error = (
                "HTTP/1.1 404 Not Found\r\n"
                "Content-Type: application/json\r\n"
                "\r\n"
                f"{error_body}"
            )
            client_socket.sendall(http_error.encode('utf-8'))

    finally:
        client_socket.close()