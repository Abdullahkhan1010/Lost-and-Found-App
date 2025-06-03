import socket
import threading
import json
import uuid
import time
import sys # Import sys for graceful exit

# Server configuration
HOST = '0.0.0.0'  # Listen on all available network interfaces
PORT = 65432
DATA_FILE = 'items.json'
BUFFER_SIZE = 4096 # Increased buffer size for potentially longer messages/item details

# Global data structures (with locks for thread safety)
items_lock = threading.Lock()
items = []  # List of item dictionaries
clients_lock = threading.Lock()
# client_connections: {client_id: {'conn': conn, 'addr': addr, 'mode': 'command'/'chat', 'chat_partner_id': None/client_id, 'reporting_item': None}}
client_connections = {}
# active_chats: {client_id_1: client_id_2, client_id_2: client_id_1}
# This helps quickly find the chat partner
chat_partners_lock = threading.Lock()
chat_partners = {}

# Global event to signal server shutdown to threads
server_running = threading.Event()
server_running.set() # Set to True initially

LOCATIONS = ["A Block", "B Block", "C Block", "Cafe", "Library", "Sports Complex", "Admin Building", "Hostel A", "Hostel B", "Other"]

def load_items():
    """Loads items from the JSON data file."""
    global items
    try:
        with items_lock:
            with open(DATA_FILE, 'r') as f:
                items = json.load(f)
            print(f"[SYSTEM] Loaded {len(items)} items from {DATA_FILE}")
    except FileNotFoundError:
        items = []
        print(f"[SYSTEM] {DATA_FILE} not found. Starting with an empty item list.")
    except json.JSONDecodeError:
        items = []
        print(f"[SYSTEM] Error decoding {DATA_FILE}. Starting with an empty item list.")

def save_items():
    """Saves the current list of items to the JSON data file."""
    with items_lock:
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump(items, f, indent=2)
            # print(f"[SYSTEM] Saved {len(items)} items to {DATA_FILE}") # Can be too verbose
        except IOError as e:
            print(f"[SYSTEM] Error saving items to {DATA_FILE}: {e}")


def find_match(new_item):
    """
    Tries to find a match for a newly reported item.
    A match occurs if name, color, and location are the same,
    and one item is 'lost' and the other is 'found',
    and neither item is already part of an active match/chat.
    """
    with items_lock:
        for item in items:
            # Check if the item is already involved in an active chat or matched
            is_item_reporter_in_chat = False
            with clients_lock:
                if item.get("reporter_id") and client_connections.get(item["reporter_id"], {}).get("mode") == "chat":
                    is_item_reporter_in_chat = True
            
            if item.get("matched_with"): # If item already has a match_id
                    continue
            if is_item_reporter_in_chat: # If reporter of this item is already in chat
                    continue

            # IMPORTANT FIX: Prevent self-matching
            if item.get("reporter_id") == new_item.get("reporter_id"):
                continue

            if (item["name"].lower() == new_item["name"].lower() and
                item["color"].lower() == new_item["color"].lower() and
                item["location"] == new_item["location"] and
                item["status"] != new_item["status"] and # One is lost, other is found
                not item.get("matched_with")): # Ensure the existing item isn't already matched

                # Check if the reporter of the existing item is still connected and not in chat
                reporter_id_existing_item = item.get("reporter_id")
                with clients_lock:
                    if reporter_id_existing_item not in client_connections or \
                       client_connections[reporter_id_existing_item]['mode'] == 'chat':
                        continue # Reporter not connected or already in chat, skip this item

                return item # Return the matched item
    return None

def notify_client(client_id, message):
    """Sends a message to a specific client."""
    # Don't acquire clients_lock here since it might already be held by the caller
    client_info = client_connections.get(client_id)
    if client_info and client_info['conn']:
        try:
            # Ensure the message ends with a newline
            if not message.endswith('\n'):
                message += '\n'
            client_info['conn'].sendall(message.encode('utf-8'))
        except socket.error as e:
            print(f"[SYSTEM] Error sending message to client {client_id}: {e}")
            # Potentially handle disconnection here or in the main client loop

def start_chat_session(client_id_1, client_id_2, item1_id, item2_id):
    """Initiates a chat session between two clients."""
    with clients_lock:
        if client_id_1 not in client_connections or client_id_2 not in client_connections:
            print("[SYSTEM] One or both clients for chat disconnected before chat could start.")
            return

        client_connections[client_id_1]['mode'] = 'chat'
        client_connections[client_id_1]['chat_partner_id'] = client_id_2
        client_connections[client_id_2]['mode'] = 'chat'
        client_connections[client_id_2]['chat_partner_id'] = client_id_1

    with chat_partners_lock:
        chat_partners[client_id_1] = client_id_2
        chat_partners[client_id_2] = client_id_1

    # Mark items as matched
    with items_lock:
        for item in items:
            if item["id"] == item1_id:
                item["matched_with"] = item2_id
                item["status"] = "matched"
            elif item["id"] == item2_id:
                item["matched_with"] = item1_id
                item["status"] = "matched"
    save_items()

    chat_instructions = "\n[CHAT] You are now connected for a chat. Type your message and press Enter.\n[CHAT] Type '/exit_chat' to end the chat and return to the main menu.\n"
    notify_client(client_id_1, f"MATCH_FOUND You have been matched with another user regarding item ID {item2_id}!\n{chat_instructions}")
    notify_client(client_id_2, f"MATCH_FOUND You have been matched with another user regarding item ID {item1_id}!\n{chat_instructions}")
    print(f"[SYSTEM] Chat session started between {client_id_1} and {client_id_2} for items {item1_id} & {item2_id}")

def end_chat_session(client_id):
    """Ends a chat session for a client and their partner."""
    print(f"[DEBUG] end_chat_session called for client {client_id}")
    
    # Get partner_id first before modifying anything
    partner_id = None
    client_conn = None
    partner_conn = None
    
    with clients_lock:
        if client_id not in client_connections:
            print(f"[DEBUG] Client {client_id} not in client_connections")
            return
        
        client_info = client_connections[client_id]
        if client_info['mode'] != 'chat':
            print(f"[DEBUG] Client {client_id} not in chat mode (mode: {client_info['mode']})")
            return
        
        partner_id = client_info.get('chat_partner_id')
        print(f"[DEBUG] Partner ID for {client_id}: {partner_id}")
        
        # Get connection objects while we have the lock
        client_conn = client_info['conn']
        if partner_id and partner_id in client_connections:
            partner_conn = client_connections[partner_id]['conn']
        
        # Update modes while we have the lock
        client_connections[client_id]['mode'] = 'command'
        client_connections[client_id]['chat_partner_id'] = None
        
        if partner_id and partner_id in client_connections:
            client_connections[partner_id]['mode'] = 'command'
            client_connections[partner_id]['chat_partner_id'] = None

    # Remove from chat_partners
    with chat_partners_lock:
        if client_id in chat_partners:
            del chat_partners[client_id]
        if partner_id and partner_id in chat_partners:
            del chat_partners[partner_id]

    # Send notifications AFTER releasing the locks
    try:
        if client_conn:
            message = "CHAT_ENDED You have left the chat. Returning to main menu.\n"
            client_conn.sendall(message.encode('utf-8'))
            print(f"[SYSTEM] Sent CHAT_ENDED to {client_id}. Mode set to command.")
    except socket.error as e:
        print(f"[SYSTEM] Error sending message to client {client_id}: {e}")

    try:
        if partner_conn and partner_id:
            message = "CHAT_ENDED The other user has left the chat. Returning to main menu.\n"
            partner_conn.sendall(message.encode('utf-8'))
            print(f"[SYSTEM] Sent CHAT_ENDED to partner {partner_id}. Chat session ended between {client_id} and {partner_id}")
    except socket.error as e:
        print(f"[SYSTEM] Error sending message to partner {partner_id}: {e}")

    if not partner_id:
        print(f"[SYSTEM] Chat session ended for {client_id}. Partner was not found or already disconnected.")
    
    print(f"[DEBUG] end_chat_session completed for {client_id}")
    # Items remain "matched" even after chat ends.
    # No need to change item status here unless a "claim" feature is added.

def handle_client(conn, addr, client_id):
    """Handles a single client connection."""
    print(f"[NEW CONNECTION] {addr} connected as {client_id}.")
    with clients_lock:
        client_connections[client_id] = {'conn': conn, 'addr': addr, 'mode': 'command', 'chat_partner_id': None}

    try:
        conn.sendall("WELCOME Welcome to the Lost & Found Service!\n".encode('utf-8'))
        conn.sendall(f"LOCATIONS {json.dumps(LOCATIONS)}\n".encode('utf-8')) # Send locations once
        
        # Set a shorter timeout for client recv operations to allow for graceful shutdown
        conn.settimeout(5.0) # 5-second timeout

        while server_running.is_set(): # Loop as long as the server is running
            with clients_lock: # Check client mode safely
                current_mode = client_connections.get(client_id, {}).get('mode', 'command')
                partner_id = client_connections.get(client_id, {}).get('chat_partner_id')

            try:
                data = conn.recv(BUFFER_SIZE)
                if not data:
                    print(f"[DISCONNECTED] Client {client_id} ({addr}) disconnected (empty data).")
                    break # Exit loop if client disconnects
                
                message = data.decode('utf-8').strip()
                print(f"[RECV {client_id} - {current_mode}] Raw message: '{data.decode('utf-8').replace('\n', '\\n')}' | Stripped message: '{message}'") # Added detailed logging for debugging

                if current_mode == 'command':
                    if message.startswith("REPORT_"):
                        parts = message.split(" ", 1)
                        command = parts[0]
                        
                        if len(parts) < 2 or not parts[1]:
                            conn.sendall("ERROR Invalid report command. Missing item data.\n".encode('utf-8'))
                            continue
                        
                        item_json_str = parts[1]
                        try:
                            item_data = json.loads(item_json_str)
                            item_data["id"] = str(uuid.uuid4()) # Generate unique ID for the item
                            item_data["reporter_id"] = client_id
                            item_data["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
                            item_data["matched_with"] = None # Initialize matched_with field

                            if command == "REPORT_LOST":
                                item_data["status"] = "lost"
                            elif command == "REPORT_FOUND":
                                item_data["status"] = "found"
                            else:
                                conn.sendall("ERROR Invalid report type.\n".encode('utf-8'))
                                continue
                            
                            # Validate essential fields
                            if not all(k in item_data for k in ("name", "color", "location", "description")):
                                conn.sendall("ERROR Missing item details (name, color, location, description).\n".encode('utf-8'))
                                continue
                            if item_data["location"] not in LOCATIONS:
                                conn.sendall(f"ERROR Invalid location. Please choose from: {', '.join(LOCATIONS)}\n".encode('utf-8'))
                                continue


                            with items_lock:
                                items.append(item_data)
                            save_items()
                            conn.sendall(f"SUCCESS Item {item_data['id']} reported successfully.\n".encode('utf-8'))
                            # FIX: Changed item['status'] to item_data['status']
                            print(f"[ITEM REPORTED] Client {client_id} reported: {item_data['name']} ({item_data['status']}) at {item_data['location']}")

                            # Check for matches
                            matched_item = find_match(item_data)
                            if matched_item:
                                print(f"[MATCH] Item {item_data['id']} matched with {matched_item['id']}")
                                # Ensure both clients are still connected and not in another chat
                                with clients_lock:
                                    reporter1_info = client_connections.get(item_data["reporter_id"])
                                    reporter2_info = client_connections.get(matched_item["reporter_id"])

                                if reporter1_info and reporter1_info['mode'] == 'command' and \
                                   reporter2_info and reporter2_info['mode'] == 'command':
                                    start_chat_session(item_data["reporter_id"], matched_item["reporter_id"], item_data["id"], matched_item["id"])
                                else:
                                    print(f"[MATCH DELAYED] Could not start chat for {item_data['id']} and {matched_item['id']} - one or both users busy/disconnected.")
                                    conn.sendall(f"INFO Your item '{item_data['name']}' has a potential match (ID: {matched_item['id']}). The other user will be notified if available.\n".encode('utf-8'))
                                    # Optionally notify the other user if they are in command mode
                                    if reporter2_info and reporter2_info['mode'] == 'command':
                                        notify_client(matched_item["reporter_id"], f"INFO Your reported item '{matched_item['name']}' (ID: {matched_item['id']}) has a new potential match (ID: {item_data['id']}).\n")

                            else:
                                conn.sendall("INFO No immediate match found. We'll keep an eye out!\n".encode('utf-8'))
                        
                        except json.JSONDecodeError:
                            conn.sendall("ERROR Invalid item data format (not JSON).\n".encode('utf-8'))
                        except Exception as e:
                            conn.sendall(f"ERROR Processing item: {str(e)}\n".encode('utf-8'))
                            print(f"[ERROR] Processing item for {client_id}: {e}")
                        
                    elif message.upper() == "GET_MY_ITEMS":
                        my_items_list = []
                        with items_lock:
                            for item in items:
                                if item.get("reporter_id") == client_id:
                                    my_items_list.append(f"ID: {item['id']}, Name: {item['name']}, Status: {item['status']}, Matched: {'Yes' if item.get('matched_with') else 'No'}")
                        if my_items_list:
                            conn.sendall(f"YOUR_ITEMS \n" + "\n".join(my_items_list) + "\nEND_YOUR_ITEMS\n".encode('utf-8'))
                        else:
                            conn.sendall("YOUR_ITEMS You have not reported any items.\nEND_YOUR_ITEMS\n".encode('utf-8'))
                    
                    elif message.upper() == "GET_ALL_ITEMS":
                        conn.sendall("ALL_ITEMS_START\n".encode('utf-8'))
                        with items_lock:
                            if items:
                                for item in items:
                                    item_summary = (
                                        f"ITEM: Type: {item['status'].capitalize()}, "
                                        f"Name: {item['name']}, "
                                        f"Color: {item['color']}, "
                                        f"Location: {item['location']}, "
                                        f"Description: {item['description']}, "
                                        f"Reported: {item['timestamp']}, "
                                        f"Matched: {'Yes' if item.get('matched_with') else 'No'}\n"
                                    )
                                    conn.sendall(item_summary.encode('utf-8'))
                            else:
                                conn.sendall("ITEM: No items reported yet.\n".encode('utf-8'))
                        conn.sendall("ALL_ITEMS_END\n".encode('utf-8'))
                        print(f"[INFO] Client {client_id} requested all items.")

                    else:
                        conn.sendall("ERROR Unknown command. Available: REPORT_LOST <json>, REPORT_FOUND <json>, GET_MY_ITEMS, GET_ALL_ITEMS\n".encode('utf-8'))
                
                elif current_mode == 'chat':
                    if message.lower() == "/exit_chat":
                        print(f"[DEBUG] Client {client_id} sent /exit_chat. Calling end_chat_session.")
                        notify_client(client_id, "INFO You are exiting the chat...")
                        end_chat_session(client_id)
                        # No need for time.sleep(0.1) here, as SHUT_WR should handle the timing.
                        # Do NOT break here. Allow the loop to continue.
                        # The client's mode is now 'command', so next messages will be handled as commands.
                    elif partner_id:
                        with clients_lock: # Ensure partner is still valid
                            if partner_id in client_connections and client_connections[partner_id]['conn']:
                                try:
                                    # Relay message
                                    client_connections[partner_id]['conn'].sendall(f"CHAT_MSG [{client_id[-6:]}]: {message}\n".encode('utf-8'))
                                except socket.error as e:
                                    print(f"[CHAT RELAY ERROR] Could not send to {partner_id}: {e}")
                                    # Notify sender that partner might have disconnected
                                    conn.sendall("SYSTEM_MSG Your chat partner may have disconnected. Ending chat.\n".encode('utf-8'))
                                    end_chat_session(client_id) # End chat for current client as well
                            else: # Partner disconnected or removed
                                conn.sendall("SYSTEM_MSG Your chat partner has disconnected. Ending chat.\n".encode('utf-8'))
                                end_chat_session(client_id)
                    else: # Should not happen if mode is chat and partner_id is None
                        conn.sendall("SYSTEM_MSG Chat error: No partner found. Ending chat.\n".encode('utf-8'))
                        end_chat_session(client_id)

            except socket.timeout:
                continue # Just continue listening
            except UnicodeDecodeError:
                print(f"[ERROR] Client {client_id} sent non-UTF-8 data.")
                conn.sendall("ERROR Invalid data encoding. Please use UTF-8.\n".encode('utf-8'))
            except ConnectionResetError:
                print(f"[DISCONNECTED] Client {client_id} ({addr}) reset the connection.")
                break # Break if client explicitly disconnects or connection is reset
            except Exception as e:
                print(f"[ERROR] Unexpected error with client {client_id} ({addr}): {e}")
                break # Break on other unexpected errors
        
    finally:
        print(f"[CLEANUP] Cleaning up for client {client_id} ({addr}).")
        # If client was in a chat, notify partner and end session
        with clients_lock:
            if client_id in client_connections and client_connections[client_id]['mode'] == 'chat':
                partner_id_on_disconnect = client_connections[client_id].get('chat_partner_id')
                print(f"[CLEANUP] Client {client_id} was in chat with {partner_id_on_disconnect}. Ending chat.")
                if partner_id_on_disconnect in client_connections:
                    client_connections[partner_id_on_disconnect]['mode'] = 'command'
                    client_connections[partner_id_on_disconnect]['chat_partner_id'] = None
                    notify_client(partner_id_on_disconnect, "CHAT_ENDED Your chat partner has disconnected. Returning to main menu.")
                    print(f"[SYSTEM] Chat session ended for {partner_id_on_disconnect} due to partner {client_id} disconnecting.")
                    with chat_partners_lock:
                        if partner_id_on_disconnect in chat_partners:
                            del chat_partners[partner_id_on_disconnect]
                        if client_id in chat_partners: # remove self from chat_partners too
                            del chat_partners[client_id]


        with clients_lock:
            if client_id in client_connections:
                del client_connections[client_id]
        
        with chat_partners_lock: # Ensure client is removed from any lingering chat partner mappings
            if client_id in chat_partners:
                lingering_partner = chat_partners.pop(client_id)
                if lingering_partner in chat_partners and chat_partners[lingering_partner] == client_id:
                    del chat_partners[lingering_partner]


        conn.close()
        print(f"[CONNECTION CLOSED] Connection with {addr} (Client {client_id}) closed.")

def main():
    """Main function to start the server."""
    load_items()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allow address reuse
    try:
        server_socket.bind((HOST, PORT))
    except socket.error as e:
        print(f"[FATAL ERROR] Could not bind to port {PORT}: {e}")
        return
        
    server_socket.listen(5) # Listen for up to 5 queued connections
    print(f"[LISTENING] Server listening on {HOST}:{PORT}")

    # Set a timeout for the accept() call to allow checking server_running flag
    server_socket.settimeout(1.0) 

    try:
        while server_running.is_set(): # Loop as long as the server is signaled to be running
            try:
                conn, addr = server_socket.accept()
                client_id = str(uuid.uuid4()) # Assign a unique ID to the client
                
                thread = threading.Thread(target=handle_client, args=(conn, addr, client_id))
                thread.daemon = True # Allow main program to exit even if threads are running
                thread.start()
            except socket.timeout:
                continue # Timeout on accept(), check server_running flag again
            except Exception as e:
                print(f"[ERROR] Error accepting new connection: {e}")
                if not server_running.is_set(): # If server is shutting down, break
                    break
    except KeyboardInterrupt:
        print("\n[SYSTEM] KeyboardInterrupt detected. Server shutting down...")
    finally:
        print("[SYSTEM] Setting server_running to False to stop client threads.")
        server_running.clear() # Signal all client threads to stop
        
        # Give a small delay for threads to notice the shutdown signal and start cleaning up
        time.sleep(1) 

        print("[SYSTEM] Saving items before shutdown...")
        save_items()
        print("[SYSTEM] Closing server socket.")
        server_socket.close()
        
        # Attempt to notify all connected clients about server shutdown
        with clients_lock:
            # Create a copy of client_connections keys to iterate over, as it might be modified
            # by threads during cleanup.
            client_ids_to_notify = list(client_connections.keys()) 
            for cid in client_ids_to_notify:
                client_info = client_connections.get(cid)
                if client_info and client_info['conn']:
                    try:
                        client_info['conn'].sendall("SERVER_SHUTDOWN The server is shutting down. Goodbye.\n".encode('utf-8'))
                        client_info['conn'].close()
                        print(f"[CLEANUP] Notified and closed connection for client {cid}")
                    except Exception as e:
                        print(f"[CLEANUP ERROR] Could not notify client {cid}: {e}")
        print("[SYSTEM] Server shutdown complete.")
        sys.exit(0) # Ensure the main process exits

if __name__ == "__main__":
    main()
