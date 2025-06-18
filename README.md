# Lost and Found App 🔍📱

A comprehensive **client-server** Lost and Found application built with **Python** and **Tkinter**. This application helps people report lost or found items, match them automatically, and enables direct communication between users through an integrated chat system.

## 🌟 Features

### 📋 Core Functionality
- **Item Reporting**: Report lost or found items with detailed descriptions
- **Smart Matching**: Automatic matching system for lost and found items
- **Real-time Chat**: Direct messaging between users who have matching items
- **Multi-location Support**: Predefined campus/building locations
- **Persistent Storage**: JSON-based data persistence for items and matches
- **User Management**: Client identification and session management

### 🎯 Key Capabilities
- **Threaded Server**: Multi-client support with thread-safe operations
- **Modern GUI**: Dark-themed Tkinter interface with professional styling
- **Item Categories**: Flexible item reporting with name, color, location, and description
- **Status Tracking**: Item status management (reported, matched, resolved)
- **Network Communication**: TCP socket-based client-server architecture
- **Cross-platform**: Works on Windows, macOS, and Linux

## 🛠️ Technology Stack

- **Language**: Python 3.x
- **GUI Framework**: Tkinter with custom styling
- **Networking**: TCP sockets with threading
- **Data Storage**: JSON file-based persistence
- **Concurrency**: Threading for multi-client support
- **Architecture**: Client-Server model

## 📁 Project Structure

```
├── server.py          # Multi-threaded server handling clients and data
├── client.py          # GUI client application with dark theme
├── items.json         # JSON database for storing items and matches
└── README.md          # Project documentation
```

## 🏗️ Architecture Overview

### Server Components (`server.py`)
- **Socket Server**: Handles multiple client connections simultaneously
- **Item Management**: CRUD operations for lost/found items
- **Matching Engine**: Automatic matching based on item attributes
- **Chat System**: Real-time messaging between matched users
- **Data Persistence**: JSON-based storage with thread-safe operations

### Client Components (`client.py`)
- **Modern GUI**: Dark-themed interface built with Tkinter
- **Report Dialog**: User-friendly forms for item reporting
- **Chat Interface**: Integrated messaging system
- **Network Handler**: Asynchronous communication with server
- **Status Management**: Real-time updates and notifications

## 🚀 Installation & Setup

### Prerequisites
- Python 3.6 or higher
- Standard Python libraries (socket, threading, tkinter, json)
- Network access for client-server communication

### Getting Started

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Abdullahkhan1010/Lost-and-Found-App.git
   cd Lost-and-Found-App
   ```

2. **Start the server**:
   ```bash
   python server.py
   ```
   The server will start on `0.0.0.0:65432` and load existing items from `items.json`.

3. **Launch the client application**:
   ```bash
   python client.py
   ```
   The GUI client will connect to the server at `127.0.0.1:65432`.

### Network Configuration

**For Local Usage** (default):
- Server: `HOST = '0.0.0.0'`, `PORT = 65432`
- Client: `SERVER_HOST = '127.0.0.1'`, `SERVER_PORT = 65432`

**For Network Usage**:
- Update `SERVER_HOST` in `client.py` to the server's IP address
- Ensure firewall allows connections on port 65432

## 📱 How to Use

### Reporting Items

1. **Launch the client application**
2. **Select item type**: Choose "Lost" or "Found"
3. **Fill item details**:
   - Item name (e.g., "Keys", "Phone", "Book")
   - Color description
   - Location where lost/found
   - Detailed description
4. **Submit report**: The item is added to the database

### Automatic Matching

The system automatically matches items based on:
- **Item name** (case-insensitive)
- **Color** (case-insensitive)
- **Location** (exact match)

When a match is found:
- Both users are notified
- A chat session is automatically initiated
- Item status changes to "matched"

### Chat System

- **Automatic Chat**: Opens when items are matched
- **Real-time Messaging**: Instant communication between users
- **User-friendly Interface**: Clean chat window with message history
- **Connection Management**: Handles disconnections gracefully

## 🏢 Supported Locations

The application includes predefined locations:
- A Block
- B Block  
- C Block
- Cafe
- Library
- Sports Complex
- Admin Building
- Hostel A
- Hostel B
- Other (custom location)

## 🔧 Configuration

### Server Settings
```python
HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 65432      # Server port
DATA_FILE = 'items.json'  # Data storage file
BUFFER_SIZE = 4096  # Network buffer size
```

### Client Settings
```python
SERVER_HOST = '127.0.0.1'  # Server IP address
SERVER_PORT = 65432        # Server port
BUFFER_SIZE = 4096         # Network buffer size
```

## 🎨 User Interface

### Dark Theme Design
- **Modern Styling**: Professional dark theme with teal accents
- **Responsive Layout**: Adaptable to different screen sizes
- **Intuitive Navigation**: Clear buttons and organized sections
- **Color Coding**: Status indicators and message types
- **Accessibility**: High contrast for better readability

### GUI Components
- **Main Window**: Item reporting and status display
- **Report Dialog**: Modal forms for item details
- **Chat Window**: Real-time messaging interface
- **Status Bar**: Connection and system status
- **Message Boxes**: Alerts and confirmations

## 🔒 Data Management

### JSON Data Structure
```json
{
  "name": "Item Name",
  "color": "Item Color",
  "location": "Location Name",
  "description": "Detailed description",
  "id": "unique-uuid",
  "reporter_id": "user-uuid",
  "timestamp": "YYYY-MM-DD HH:MM:SS",
  "matched_with": "matched-item-id",
  "status": "reported|matched|resolved"
}
```

### Thread Safety
- **Locks**: All shared data structures use threading locks
- **Atomic Operations**: Database operations are thread-safe
- **Client Management**: Concurrent client handling without conflicts

## 🌐 Network Protocol

### Message Types
- `REPORT_ITEM`: Submit new lost/found item
- `GET_LOCATIONS`: Retrieve available locations
- `START_CHAT`: Initialize chat session
- `SEND_MESSAGE`: Send chat message
- `DISCONNECT`: Clean disconnection

### Response Codes
- `SUCCESS`: Operation completed successfully
- `ERROR`: Operation failed with error message
- `MATCH_FOUND`: Automatic item match detected
- `CHAT_MESSAGE`: Incoming chat message

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🔮 Future Enhancements

- [ ] **Database Integration**: MySQL/PostgreSQL support
- [ ] **Web Interface**: Browser-based client
- [ ] **Image Upload**: Photo attachments for items
- [ ] **Email Notifications**: Alert system for matches
- [ ] **Mobile App**: Android/iOS companion apps
- [ ] **Admin Dashboard**: Administrative management interface
- [ ] **Advanced Search**: Fuzzy matching and filters
- [ ] **User Accounts**: Registration and profile management

## 🐛 Troubleshooting

### Common Issues

**Connection Refused**:
- Ensure server is running before starting client
- Check firewall settings and port availability
- Verify IP address configuration

**GUI Issues**:
- Update Python and Tkinter to latest versions
- Check display settings and screen resolution
- Ensure proper theme support

**Data Loss**:
- Backup `items.json` regularly
- Check file permissions and disk space
- Monitor server logs for errors

## 📞 Support

For questions, bug reports, or support:

**Abdullah Khan**
- GitHub: [@Abdullahkhan1010](https://github.com/Abdullahkhan1010)
- Email: abdullah.khan1010@gmail.com

---

⭐ **Star this repository if you found it helpful!**

Made with ❤️ using Python & Tkinter
