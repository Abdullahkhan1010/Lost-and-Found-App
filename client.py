import socket
import json
import threading
import sys
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import queue

SERVER_HOST = '127.0.0.1'  # Change to server's IP if not local
SERVER_PORT = 65432
BUFFER_SIZE = 4096

# Dark theme color palette
COLORS = {
    'bg_primary': '#2b2b2b',      # Main background
    'bg_secondary': '#3c3c3c',    # Secondary background
    'bg_tertiary': '#4a4a4a',     # Tertiary background
    'fg_primary': '#ffffff',      # Main text
    'fg_secondary': '#cccccc',    # Secondary text
    'fg_accent': '#00d4aa',       # Accent color (teal)
    'fg_success': '#4caf50',      # Success green
    'fg_warning': '#ff9800',      # Warning orange
    'fg_error': '#f44336',        # Error red
    'fg_info': '#2196f3',         # Info blue
    'border': '#555555',          # Border color
    'button_hover': '#555555',    # Button hover
    'entry_bg': '#404040',        # Entry background
    'entry_fg': '#ffffff',        # Entry text
}

class ReportItemDialog(tk.Toplevel):
    """Dialog for reporting a new lost or found item."""
    def __init__(self, parent, item_type, locations_list, callback):
        super().__init__(parent)
        self.transient(parent)
        self.title(f"Report {item_type.capitalize()} Item")
        self.parent = parent
        self.item_type = item_type
        self.locations_list = locations_list if locations_list else ["Default Location (Server Down?)"]
        self.callback = callback
        self.result = None

        # Configure dialog window
        self.configure(bg=COLORS['bg_primary'])
        self.geometry("500x400")
        self.resizable(True, True)
        self.grab_set()

        self.create_dialog_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_cancel) 
        self.wait_window(self)

    def create_dialog_widgets(self):
        # Main container with padding
        main_frame = tk.Frame(self, bg=COLORS['bg_primary'], padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = tk.Label(main_frame, 
                             text=f"📋 Report {self.item_type.capitalize()} Item",
                             font=('Segoe UI', 16, 'bold'),
                             fg=COLORS['fg_accent'],
                             bg=COLORS['bg_primary'])
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky="w")

        # Item Name
        tk.Label(main_frame, text="📝 Item Name:",
                font=('Segoe UI', 10, 'bold'),
                fg=COLORS['fg_primary'],
                bg=COLORS['bg_primary']).grid(row=1, column=0, padx=(0,10), pady=8, sticky="w")
        
        self.name_entry = tk.Entry(main_frame, width=35,
                                  font=('Segoe UI', 10),
                                  bg=COLORS['entry_bg'],
                                  fg=COLORS['entry_fg'],
                                  insertbackground=COLORS['fg_accent'],
                                  relief='flat',
                                  bd=2)
        self.name_entry.grid(row=1, column=1, padx=5, pady=8, sticky="ew")
        self.name_entry.focus_set()

        # Color
        tk.Label(main_frame, text="🎨 Color:",
                font=('Segoe UI', 10, 'bold'),
                fg=COLORS['fg_primary'],
                bg=COLORS['bg_primary']).grid(row=2, column=0, padx=(0,10), pady=8, sticky="w")
        
        self.color_entry = tk.Entry(main_frame, width=35,
                                   font=('Segoe UI', 10),
                                   bg=COLORS['entry_bg'],
                                   fg=COLORS['entry_fg'],
                                   insertbackground=COLORS['fg_accent'],
                                   relief='flat',
                                   bd=2)
        self.color_entry.grid(row=2, column=1, padx=5, pady=8, sticky="ew")

        # Location
        tk.Label(main_frame, text="📍 Location:",
                font=('Segoe UI', 10, 'bold'),
                fg=COLORS['fg_primary'],
                bg=COLORS['bg_primary']).grid(row=3, column=0, padx=(0,10), pady=8, sticky="w")
        
        # Custom styled combobox for location
        self.location_var = tk.StringVar(self)
        if self.locations_list:
            self.location_var.set(self.locations_list[0])
        
        location_frame = tk.Frame(main_frame, bg=COLORS['bg_primary'])
        location_frame.grid(row=3, column=1, padx=5, pady=8, sticky="ew")
        
        self.location_combo = ttk.Combobox(location_frame, 
                                          textvariable=self.location_var,
                                          values=self.locations_list,
                                          state="readonly",
                                          font=('Segoe UI', 10),
                                          width=32)
        self.location_combo.pack(fill=tk.X)
        
        # Custom Location
        tk.Label(main_frame, text="🗺️ Custom Location:",
                font=('Segoe UI', 10),
                fg=COLORS['fg_secondary'],
                bg=COLORS['bg_primary']).grid(row=4, column=0, padx=(0,10), pady=8, sticky="w")
        
        self.custom_location_entry = tk.Entry(main_frame, width=35,
                                             font=('Segoe UI', 10),
                                             bg=COLORS['entry_bg'],
                                             fg=COLORS['entry_fg'],
                                             insertbackground=COLORS['fg_accent'],
                                             relief='flat',
                                             bd=2)
        self.custom_location_entry.grid(row=4, column=1, padx=5, pady=8, sticky="ew")

        # Description
        tk.Label(main_frame, text="📄 Description:",
                font=('Segoe UI', 10, 'bold'),
                fg=COLORS['fg_primary'],
                bg=COLORS['bg_primary']).grid(row=5, column=0, padx=(0,10), pady=8, sticky="nw")
        
        desc_frame = tk.Frame(main_frame, bg=COLORS['bg_secondary'], relief='flat', bd=2)
        desc_frame.grid(row=5, column=1, padx=5, pady=8, sticky="ew")
        
        self.desc_text = tk.Text(desc_frame, width=32, height=4,
                                font=('Segoe UI', 10),
                                bg=COLORS['entry_bg'],
                                fg=COLORS['entry_fg'],
                                insertbackground=COLORS['fg_accent'],
                                relief='flat',
                                bd=0,
                                wrap=tk.WORD)
        desc_scrollbar = tk.Scrollbar(desc_frame, orient=tk.VERTICAL, command=self.desc_text.yview)
        self.desc_text.config(yscrollcommand=desc_scrollbar.set)
        
        self.desc_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        desc_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Buttons
        button_frame = tk.Frame(main_frame, bg=COLORS['bg_primary'])
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        self.create_styled_button(button_frame, "✅ Submit", self.on_submit, COLORS['fg_success']).pack(side=tk.LEFT, padx=10)
        self.create_styled_button(button_frame, "❌ Cancel", self.on_cancel, COLORS['fg_error']).pack(side=tk.LEFT, padx=10)

        main_frame.columnconfigure(1, weight=1)

    def create_styled_button(self, parent, text, command, color):
        button = tk.Button(parent, text=text,
                          command=command,
                          font=('Segoe UI', 10, 'bold'),
                          bg=COLORS['bg_secondary'],
                          fg=color,
                          activebackground=COLORS['button_hover'],
                          activeforeground=color,
                          relief='flat',
                          bd=0,
                          padx=20,
                          pady=8,
                          cursor='hand2')
        
        # Hover effects
        def on_enter(e):
            button.config(bg=COLORS['button_hover'])
        def on_leave(e):
            button.config(bg=COLORS['bg_secondary'])
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        
        return button

    def on_submit(self):
        name = self.name_entry.get().strip()
        color = self.color_entry.get().strip()
        
        location = self.custom_location_entry.get().strip()
        if not location:
            location = self.location_var.get()
            if location == "N/A" or location == "Default Location (Server Down?)":
                messagebox.showerror("Input Error", "Please select or enter a valid location.", parent=self)
                return

        description = self.desc_text.get("1.0", tk.END).strip()

        if not all([name, color, location, description]):
            messagebox.showerror("Input Error", "All fields (Name, Color, Location, Description) are required.", parent=self)
            return

        self.result = {
            "name": name,
            "color": color,
            "location": location,
            "description": description
        }
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()

class ChatWindow(tk.Toplevel):
    """A separate window for an active chat session."""
    def __init__(self, parent_app, partner_info_str):
        super().__init__(parent_app.root)
        self.parent_app = parent_app
        self.title("💬 Chat Session")
        self.geometry("600x500")
        self.configure(bg=COLORS['bg_primary'])
        self.transient(parent_app.root)
        self.grab_set()

        self.create_chat_widgets(partner_info_str)
        self.protocol("WM_DELETE_WINDOW", self.handle_exit_request)

    def create_chat_widgets(self, partner_info_str):
        # Main container
        main_frame = tk.Frame(self, bg=COLORS['bg_primary'], padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header with partner info
        header_frame = tk.Frame(main_frame, bg=COLORS['bg_secondary'], relief='flat', bd=2)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(header_frame, 
                text=f"💬 {partner_info_str}",
                font=('Segoe UI', 12, 'bold'),
                fg=COLORS['fg_accent'],
                bg=COLORS['bg_secondary'],
                pady=10).pack()

        # Chat Display Area
        chat_frame = tk.Frame(main_frame, bg=COLORS['bg_secondary'], relief='flat', bd=2)
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        self.chat_display = tk.Text(chat_frame, 
                                   font=('Segoe UI', 10),
                                   bg=COLORS['bg_tertiary'],
                                   fg=COLORS['fg_primary'],
                                   insertbackground=COLORS['fg_accent'],
                                   relief='flat',
                                   bd=0,
                                   wrap=tk.WORD,
                                   state=tk.DISABLED,
                                   padx=10,
                                   pady=10)
        
        chat_scrollbar = tk.Scrollbar(chat_frame, orient=tk.VERTICAL, command=self.chat_display.yview)
        self.chat_display.config(yscrollcommand=chat_scrollbar.set)
        
        self.chat_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        chat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.configure_tags()

        # Input Area
        input_frame = tk.Frame(main_frame, bg=COLORS['bg_primary'])
        input_frame.pack(fill=tk.X, pady=(0, 10))

        self.chat_input_entry = tk.Entry(input_frame,
                                        font=('Segoe UI', 11),
                                        bg=COLORS['entry_bg'],
                                        fg=COLORS['entry_fg'],
                                        insertbackground=COLORS['fg_accent'],
                                        relief='flat',
                                        bd=2)
        self.chat_input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.chat_input_entry.bind("<Return>", self.send_chat_message_event)
        self.chat_input_entry.focus_set()

        self.send_chat_button = self.create_styled_button(input_frame, "📤 Send", 
                                                         self.send_chat_message_event, 
                                                         COLORS['fg_accent'])
        self.send_chat_button.pack(side=tk.RIGHT)

        # Exit Chat Button
        self.exit_button = self.create_styled_button(main_frame, "🚪 Exit Chat", 
                                                    self.handle_exit_request, 
                                                    COLORS['fg_warning'])
        self.exit_button.pack(pady=(0, 5))

    def create_styled_button(self, parent, text, command, color):
        button = tk.Button(parent, text=text,
                          command=command,
                          font=('Segoe UI', 10, 'bold'),
                          bg=COLORS['bg_secondary'],
                          fg=color,
                          activebackground=COLORS['button_hover'],
                          activeforeground=color,
                          relief='flat',
                          bd=0,
                          padx=15,
                          pady=8,
                          cursor='hand2')
        
        def on_enter(e):
            button.config(bg=COLORS['button_hover'])
        def on_leave(e):
            button.config(bg=COLORS['bg_secondary'])
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        
        return button

    def configure_tags(self):
        self.chat_display.tag_configure("user_msg", foreground=COLORS['fg_success'], font=('Segoe UI', 10, 'bold'))
        self.chat_display.tag_configure("partner_msg", foreground=COLORS['fg_info'], font=('Segoe UI', 10))
        self.chat_display.tag_configure("system_chat_msg", foreground=COLORS['fg_warning'], font=('Segoe UI', 9, 'italic'))

    def display_message_in_chat(self, message, tag=None):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, message + "\n", tag)
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def send_chat_message_event(self, event=None):
        message = self.chat_input_entry.get().strip()
        if message:
            self.parent_app.send_to_server(message + "\n") 
            self.display_message_in_chat(f"You: {message}", "user_msg")
            self.chat_input_entry.delete(0, tk.END)
            if message.lower() == "/exit_chat":
                self.display_message_in_chat("You sent /exit_chat. Waiting for server...", "system_chat_msg")
                self.send_chat_button.config(state=tk.DISABLED)
                self.chat_input_entry.config(state=tk.DISABLED)

    def handle_exit_request(self):
        self.display_message_in_chat("Sending exit command...", "system_chat_msg")
        self.parent_app.send_to_server("/exit_chat\n")
        self.send_chat_button.config(state=tk.DISABLED)
        self.chat_input_entry.config(state=tk.DISABLED)
        self.exit_button.config(state=tk.DISABLED)

class LostFoundApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🔍 Lost & Found Client")
        self.root.geometry("900x700")
        self.root.configure(bg=COLORS['bg_primary'])
        
        # Configure style
        self.setup_styles()

        self.client_socket = None
        self.receiver_thread = None
        self.stop_receiver_event = threading.Event()
        self.message_queue = queue.Queue()
        self.active_chat_window = None
        self.available_locations = []
        
        # Add loading state management
        self.loading_items = False

        self.create_widgets()
        self.connect_to_server()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.check_message_queue()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure ttk styles for dark theme
        style.configure('Dark.TCombobox',
                       fieldbackground=COLORS['entry_bg'],
                       background=COLORS['bg_secondary'],
                       foreground=COLORS['fg_primary'],
                       bordercolor=COLORS['border'],
                       arrowcolor=COLORS['fg_accent'])

    def create_widgets(self):
        # Main container with gradient-like effect
        main_frame = tk.Frame(self.root, bg=COLORS['bg_primary'], padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header section
        header_frame = tk.Frame(main_frame, bg=COLORS['bg_secondary'], relief='flat', bd=2)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = tk.Label(header_frame, 
                              text="🔍 Lost & Found Service",
                              font=('Segoe UI', 20, 'bold'),
                              fg=COLORS['fg_accent'],
                              bg=COLORS['bg_secondary'],
                              pady=15)
        title_label.pack()

        # Display area with custom styling
        display_frame = tk.Frame(main_frame, bg=COLORS['bg_secondary'], relief='flat', bd=2)
        display_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        self.display_area = tk.Text(display_frame,
                                   font=('Consolas', 10),
                                   bg=COLORS['bg_tertiary'],
                                   fg=COLORS['fg_primary'],
                                   insertbackground=COLORS['fg_accent'],
                                   relief='flat',
                                   bd=0,
                                   wrap=tk.WORD,
                                   state=tk.DISABLED,
                                   padx=15,
                                   pady=15)
        
        display_scrollbar = tk.Scrollbar(display_frame, orient=tk.VERTICAL, command=self.display_area.yview)
        self.display_area.config(yscrollcommand=display_scrollbar.set)
        
        self.display_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        display_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.configure_main_display_tags()

        # Buttons section
        buttons_frame = tk.Frame(main_frame, bg=COLORS['bg_primary'])
        buttons_frame.pack(fill=tk.X, pady=10)

        # Create beautiful gradient-style buttons
        self.report_lost_button = self.create_gradient_button(buttons_frame, "📋 Report LOST Item", 
                                                             lambda: self.show_report_item_dialog("lost"), 
                                                             COLORS['fg_error'])
        self.report_lost_button.pack(side=tk.LEFT, padx=8, expand=True, fill=tk.X)

        self.report_found_button = self.create_gradient_button(buttons_frame, "✅ Report FOUND Item", 
                                                              lambda: self.show_report_item_dialog("found"), 
                                                              COLORS['fg_success'])
        self.report_found_button.pack(side=tk.LEFT, padx=8, expand=True, fill=tk.X)
        
        self.view_all_items_button = self.create_gradient_button(buttons_frame, "📋 View All Items", 
                                                                self.request_all_items, 
                                                                COLORS['fg_info'])
        self.view_all_items_button.pack(side=tk.LEFT, padx=8, expand=True, fill=tk.X)

    def create_gradient_button(self, parent, text, command, color):
        button = tk.Button(parent, text=text,
                          command=command,
                          font=('Segoe UI', 12, 'bold'),
                          bg=COLORS['bg_secondary'],
                          fg=color,
                          activebackground=COLORS['button_hover'],
                          activeforeground=color,
                          relief='flat',
                          bd=0,
                          padx=25,
                          pady=12,
                          cursor='hand2')
        
        # Enhanced hover effects
        def on_enter(e):
            if button['state'] != tk.DISABLED:
                button.config(bg=COLORS['button_hover'], 
                             relief='raised', bd=2)
        def on_leave(e):
            if button['state'] != tk.DISABLED:
                button.config(bg=COLORS['bg_secondary'], 
                             relief='flat', bd=0)
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        
        return button

    def configure_main_display_tags(self):
        self.display_area.tag_configure("server_msg", foreground=COLORS['fg_info'], font=('Consolas', 10))
        self.display_area.tag_configure("error_msg", foreground=COLORS['fg_error'], font=('Consolas', 10, 'bold'))
        self.display_area.tag_configure("system_msg", foreground=COLORS['fg_warning'], font=('Consolas', 10, 'italic'))
        self.display_area.tag_configure("match_msg", foreground=COLORS['fg_accent'], font=('Consolas', 11, 'bold'))
        self.display_area.tag_configure("user_action", foreground=COLORS['fg_success'], font=('Consolas', 10, 'italic'))
        self.display_area.tag_configure("all_items_header", foreground=COLORS['fg_accent'], font=('Consolas', 12, 'bold'))
        self.display_area.tag_configure("all_item_entry", foreground=COLORS['fg_secondary'], font=('Consolas', 9))
        self.display_area.tag_configure("loading_msg", foreground=COLORS['fg_warning'], font=('Consolas', 10, 'bold'))

    def display_message_main(self, message, tag=None):
        self.display_area.config(state=tk.NORMAL)
        timestamp = time.strftime("[%H:%M:%S] ")
        self.display_area.insert(tk.END, timestamp + message + "\n", tag)
        self.display_area.config(state=tk.DISABLED)
        self.display_area.see(tk.END)
        # Force GUI update
        self.root.update_idletasks()

    def connect_to_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((SERVER_HOST, SERVER_PORT))
            self.client_socket.settimeout(1.0) 
            self.display_message_main(f"🌐 Connected to server at {SERVER_HOST}:{SERVER_PORT}", "system_msg")

            self.stop_receiver_event.clear()
            self.receiver_thread = threading.Thread(target=self.receive_messages_thread, args=(self.client_socket,))
            self.receiver_thread.daemon = True
            self.receiver_thread.start()
        except socket.error as e:
            self.display_message_main(f"❌ Could not connect to server: {e}", "error_msg")
            messagebox.showerror("Connection Error", f"Could not connect to server: {e}")
            self.root.quit()

    def receive_messages_thread(self, sock):
        while not self.stop_receiver_event.is_set():
            try:
                response = sock.recv(BUFFER_SIZE)
                if not response:
                    self.message_queue.put(("CONNECTION_LOST", "🔌 Connection lost to server."))
                    break
                
                decoded_response = response.decode('utf-8')
                messages = decoded_response.split('\n') 

                for msg_raw in messages:
                    msg = msg_raw.strip()
                    if not msg:
                        continue
                    self.message_queue.put(("SERVER_DATA", msg))

            except socket.timeout:
                continue 
            except ConnectionResetError:
                self.message_queue.put(("CONNECTION_LOST", "🔌 Connection reset by server."))
                break
            except Exception as e:
                if not self.stop_receiver_event.is_set(): 
                    self.message_queue.put(("RECEIVE_ERROR", f"❌ Error receiving data: {e}"))
                break
        
        if sock:
            try: sock.close()
            except Exception: pass 
        self.message_queue.put(("THREAD_STOPPED", "🛑 Message receiver thread stopped."))

    def check_message_queue(self):
        processed_count = 0
        max_per_cycle = 50  # Limit messages processed per cycle to keep UI responsive
        
        try:
            while processed_count < max_per_cycle:
                msg_type, data = self.message_queue.get_nowait()
                self.process_server_message(msg_type, data)
                processed_count += 1
        except queue.Empty:
            pass 
        
        if not self.stop_receiver_event.is_set():
            # Check more frequently during loading
            delay = 50 if self.loading_items else 100
            self.root.after(delay, self.check_message_queue)

    def process_server_message(self, msg_type, data):
        if msg_type == "CONNECTION_LOST" or msg_type == "RECEIVE_ERROR":
            self.display_message_main(data, "error_msg")
            if self.active_chat_window:
                self.active_chat_window.display_message_in_chat("Connection to server lost. Chat ended.", "system_chat_msg")
                self.active_chat_window.destroy()
                self.active_chat_window = None
            self.update_main_window_buttons_state()
            self.stop_receiver_event.set() 
            messagebox.showerror("Connection Error", data)
            self.disable_all_controls_on_disconnect()
            return
        elif msg_type == "THREAD_STOPPED":
            self.display_message_main(data, "system_msg")
            return
        elif msg_type == "SERVER_DATA":
            msg = data 
            if msg.startswith("WELCOME"):
                self.display_message_main(f"🎉 {msg.split(' ', 1)[1]}", "server_msg")
            elif msg.startswith("LOCATIONS"):
                try:
                    locations_json = msg.split(" ", 1)[1]
                    self.available_locations = json.loads(locations_json)
                    self.display_message_main(f"📍 Received available locations.", "system_msg")
                except (IndexError, json.JSONDecodeError) as e:
                    self.display_message_main(f"❌ Could not parse locations: {e}", "error_msg")
            elif msg.startswith("MATCH_FOUND"):
                partner_info = msg.split(' ', 1)[1]
                self.display_message_main(f"🎯 {partner_info}", "match_msg")
                if not self.active_chat_window:
                    self.active_chat_window = ChatWindow(self, partner_info)
                else:
                    self.active_chat_window.display_message_in_chat(f"New match info: {partner_info}", "system_chat_msg")
                self.update_main_window_buttons_state()
            elif msg.startswith("CHAT_MSG"):
                if self.active_chat_window:
                    try:
                        content = msg.split(" ", 1)[1]
                        self.active_chat_window.display_message_in_chat(content, "partner_msg") 
                    except IndexError:
                        self.active_chat_window.display_message_in_chat(msg, "partner_msg") 
                else:
                    self.display_message_main(f"💬 [UNHANDLED] {msg}", "error_msg")
            elif msg.startswith("CHAT_ENDED"):
                self.display_message_main(f"🚪 {msg.split(' ', 1)[1]}", "server_msg")
                if self.active_chat_window:
                    self.active_chat_window.display_message_in_chat("Chat session ended by server.", "system_chat_msg")
                    self.active_chat_window.destroy()
                    self.active_chat_window = None
                self.update_main_window_buttons_state()
            elif msg.startswith("SYSTEM_MSG") or msg.startswith("INFO") or msg.startswith("SUCCESS"):
                self.display_message_main(f"ℹ️ {msg.split(' ', 1)[1] if ' ' in msg else msg}", "server_msg")
            elif msg.startswith("ERROR"):
                self.display_message_main(f"❌ {msg.split(' ', 1)[1] if ' ' in msg else msg}", "error_msg")
            elif msg.startswith("ALL_ITEMS_START"):
                self.loading_items = True
                self.display_message_main("\n📋 ═══ All Reported Items ═══", "all_items_header")
                self.display_message_main("⏳ Loading items...", "loading_msg")
                # Update button state to show loading
                self.view_all_items_button.config(text="⏳ Loading...", state=tk.DISABLED, 
                                                 bg=COLORS['bg_tertiary'], fg=COLORS['fg_secondary'])
            elif msg.startswith("ALL_ITEMS_END"):
                self.loading_items = False
                self.display_message_main("✅ All items loaded successfully!", "loading_msg")
                self.display_message_main("══════════════════════════", "all_items_header")
                # Restore button state
                self.view_all_items_button.config(text="📋 View All Items", state=tk.NORMAL,
                                                 bg=COLORS['bg_secondary'], fg=COLORS['fg_info'])
            elif msg.startswith("ITEM:"):
                item_details = msg.split("ITEM: ", 1)[1]
                self.display_message_main(f"  📌 {item_details}", "all_item_entry")
            elif msg == "SERVER_SHUTDOWN The server is shutting down. Goodbye.":
                self.display_message_main(f"🛑 {msg}", "error_msg")
                self.stop_receiver_event.set()
                if self.active_chat_window:
                    self.active_chat_window.destroy()
                    self.active_chat_window = None
                messagebox.showinfo("Server Shutdown", "The server is shutting down. The application will close.")
                self.root.quit()
            else:
                if not any(msg.startswith(prefix) for prefix in ["YOUR_ITEMS", "END_YOUR_ITEMS", "ALL_ITEMS_START", "ALL_ITEMS_END", "ITEM:"]):
                    self.display_message_main(msg, "server_msg") 
    
    def disable_all_controls_on_disconnect(self):
        self.report_lost_button.config(state=tk.DISABLED, bg=COLORS['bg_tertiary'], fg=COLORS['fg_secondary'])
        self.report_found_button.config(state=tk.DISABLED, bg=COLORS['bg_tertiary'], fg=COLORS['fg_secondary'])
        self.view_all_items_button.config(state=tk.DISABLED, bg=COLORS['bg_tertiary'], fg=COLORS['fg_secondary'])

    def update_main_window_buttons_state(self):
        if self.active_chat_window or self.loading_items:
            self.report_lost_button.config(state=tk.DISABLED, bg=COLORS['bg_tertiary'], fg=COLORS['fg_secondary'])
            self.report_found_button.config(state=tk.DISABLED, bg=COLORS['bg_tertiary'], fg=COLORS['fg_secondary'])
            if not self.loading_items:  # Don't change view button if it's in loading state
                self.view_all_items_button.config(state=tk.DISABLED, bg=COLORS['bg_tertiary'], fg=COLORS['fg_secondary'])
        else:
            if self.client_socket and not self.stop_receiver_event.is_set():
                self.report_lost_button.config(state=tk.NORMAL, bg=COLORS['bg_secondary'], fg=COLORS['fg_error'])
                self.report_found_button.config(state=tk.NORMAL, bg=COLORS['bg_secondary'], fg=COLORS['fg_success'])
                self.view_all_items_button.config(state=tk.NORMAL, bg=COLORS['bg_secondary'], fg=COLORS['fg_info'])
            else:
                self.disable_all_controls_on_disconnect()

    def send_to_server(self, message):
        if self.client_socket and not self.stop_receiver_event.is_set():
            try:
                self.client_socket.sendall(message.encode('utf-8'))
            except socket.error as e:
                self.display_message_main(f"❌ Could not send message: {e}", "error_msg")
                self.message_queue.put(("CONNECTION_LOST", f"🔌 Connection error on send: {e}"))
        else:
            self.display_message_main("❌ Not connected to server.", "error_msg")

    def show_report_item_dialog(self, item_type):
        if self.active_chat_window:
            messagebox.showinfo("Action Blocked", "Please close the active chat window before reporting an item.", parent=self.root)
            return
        if self.loading_items:
            messagebox.showinfo("Action Blocked", "Please wait for the current operation to complete.", parent=self.root)
            return
        dialog = ReportItemDialog(self.root, item_type, self.available_locations, self.submit_item_report)
        if dialog.result:
            self.submit_item_report(item_type, dialog.result)

    def submit_item_report(self, item_type, item_details):
        if item_details:
            command = f"REPORT_{item_type.upper()} {json.dumps(item_details)}\n"
            self.send_to_server(command)
            emoji = "❌" if item_type == "lost" else "✅"
            self.display_message_main(f"{emoji} Reported {item_type} item: {item_details['name']}", "user_action")

    def request_all_items(self, event=None):
        if self.active_chat_window:
            messagebox.showinfo("Action Blocked", "Please close the active chat window first.", parent=self.root)
            return
        if self.loading_items:
            messagebox.showinfo("Please Wait", "Items are already being loaded. Please wait...", parent=self.root)
            return
        
        self.send_to_server("GET_ALL_ITEMS\n")
        self.display_message_main("📋 Requested all reported items.", "user_action")
        # The loading state will be set when ALL_ITEMS_START is received

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.display_message_main("🔌 Disconnecting...", "system_msg")
            self.stop_receiver_event.set() 
            
            if self.active_chat_window:
                try:
                    self.active_chat_window.destroy()
                except tk.TclError: pass
                self.active_chat_window = None

            if self.receiver_thread and self.receiver_thread.is_alive():
                self.receiver_thread.join(timeout=1.0) 

            if self.client_socket:
                try:
                    self.client_socket.shutdown(socket.SHUT_RDWR)
                except (OSError, socket.error): pass 
                finally:
                    try: self.client_socket.close()
                    except socket.error: pass 
            self.root.destroy()
            sys.exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = LostFoundApp(root)
    root.mainloop()
