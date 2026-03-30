⛏️ Minecraft Server Controller
A lightweight, Python-based script (server.py) to manage and launch your Minecraft server instance with ease.

🚀 Quick Start
Prerequisites
Python 3.x installed.

Java (version matching your Minecraft server requirements).

The server.jar file located in the same directory.

Installation
Clone this repository:

```Bash
git clone https://github.com/your-username/your-repo-name.git
cd MinecraftServer
```
Place your server.py in the root folder.

Ensure server.py has execution permissions.

Usage
Run the "StartServer.bat" to start the server:

```bash
python server.py
```
📂 Project Structure
server.py: The main Python script that handles the JVM arguments and server lifecycle.

server.properties: (Generated) Minecraft configuration settings.

world/: (Generated) Your world data.

logs/: Check here if something crashes!

⚙️ Configuration
You can modify the memory allocation or flags directly inside server.py. Look for the following variables:

RAM Allocation: e.g., -Xmx2G -Xms1G

EULA: Ensure eula.txt is set to true after the first run.
