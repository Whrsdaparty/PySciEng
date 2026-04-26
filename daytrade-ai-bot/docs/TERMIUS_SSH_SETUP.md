# Termius SSH Setup

This guide is for running the Daytrade AI Bot from an Android phone using **Termius**.

## Key point

Termius is an SSH client. The commands run on the remote computer/server you connect to through SSH. Termius itself is not the same thing as Termux and should not be treated as a local Android Linux package manager.

Use Termius when you want to run the project on:

- A home Linux desktop or laptop
- A Raspberry Pi
- A VPS/cloud server
- A workbench machine on your local network

Use Termux instead if you want to run Python directly inside Android without SSH.

---

## Recommended remote machine

Use Ubuntu/Debian Linux first. It will be the easiest target for Python, FastAPI, SQLite, and browser access.

---

## 1. Connect in Termius

In Termius, create a host using:

```text
Host/IP: your server IP address
Port: 22
Username: your Linux username
Password or SSH key: your login credential
```

Then open the saved host.

---

## 2. Install system dependencies on the remote Linux machine

For Ubuntu/Debian:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git python3 python3-venv python3-pip build-essential sqlite3
```

Optional but useful:

```bash
sudo apt install -y curl nano htop ufw
```

---

## 3. Clone the repository

```bash
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/Whrsdaparty/PySciEng.git
cd PySciEng/daytrade-ai-bot
```

If the repo already exists:

```bash
cd ~/projects/PySciEng
git pull
cd daytrade-ai-bot
```

---

## 4. Create Python virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -e .[dev]
```

---

## 5. Run the web app

For phone-only testing through Termius, bind to all interfaces:

```bash
uvicorn daytrade_ai_bot.web.app:app --host 0.0.0.0 --port 8000
```

If you are testing only from the same remote machine:

```bash
uvicorn daytrade_ai_bot.web.app:app --host 127.0.0.1 --port 8000
```

Avoid `--reload` at first when working from a mobile SSH client. It is useful during development, but it can be noisy and less stable over mobile sessions.

---

## 6. Open the dashboard from Android

If the remote machine is on your local network, open this in your Android browser:

```text
http://SERVER_IP_ADDRESS:8000
```

Example:

```text
http://192.168.1.50:8000
```

If using a cloud server, open:

```text
http://PUBLIC_SERVER_IP:8000
```

Only expose this carefully. For real use, put it behind authentication, HTTPS, and a firewall.

---

## 7. Firewall note

For local network testing, you may need to allow port 8000 on the remote machine.

Ubuntu UFW example:

```bash
sudo ufw allow 8000/tcp
sudo ufw status
```

For public/cloud servers, avoid exposing the app broadly until authentication is added.

---

## 8. Database files

The app creates these local files on the remote machine:

```text
data/simulation_trading.sqlite3
data/real_investing.sqlite3
```

Keep backups if you enter important trade data.

---

## 9. Useful Termius workflow

Recommended Termius snippets:

### Start app

```bash
cd ~/projects/PySciEng/daytrade-ai-bot && source .venv/bin/activate && uvicorn daytrade_ai_bot.web.app:app --host 0.0.0.0 --port 8000
```

### Update app

```bash
cd ~/projects/PySciEng && git pull && cd daytrade-ai-bot && source .venv/bin/activate && pip install -e .[dev]
```

### Check database files

```bash
cd ~/projects/PySciEng/daytrade-ai-bot && ls -lah data
```

---

## 10. Current limitation

The app currently does not have login/authentication. Treat it as a local/private tool until authentication is added.
