# Setting Up Remote Access to Raspberry Pi 3

## Option 1: SSH (Recommended for Development)

SSH is the most efficient way to work remotely on your Pi.

### On Raspberry Pi 3:

1. **Enable SSH** (if not already enabled):
   ```bash
   sudo systemctl enable ssh
   sudo systemctl start ssh
   ```

2. **Find your Pi's IP address**:
   ```bash
   hostname -I
   # or
   ip addr show
   ```

3. **Set a static IP** (optional but recommended):
   Edit `/etc/dhcpcd.conf`:
   ```bash
   sudo nano /etc/dhcpcd.conf
   ```
   Add at the end:
   ```
   interface wlan0  # or eth0 for ethernet
   static ip_address=192.168.1.100/24
   static routers=192.168.1.1
   static domain_name_servers=192.168.1.1 8.8.8.8
   ```
   Adjust IP addresses to match your network.

### On Your Development Machine:

1. **Connect via SSH**:
   ```bash
   ssh pi@<PI_IP_ADDRESS>
   # Default password is usually "raspberry" (change it!)
   ```

2. **Set up SSH key authentication** (passwordless login):
   ```bash
   # On your dev machine, generate key if you don't have one:
   ssh-keygen -t ed25519 -C "your_email@example.com"
   
   # Copy key to Pi:
   ssh-copy-id pi@<PI_IP_ADDRESS>
   ```

3. **Use VS Code Remote SSH** (if using VS Code/Cursor):
   - Install "Remote - SSH" extension
   - Press F1, type "Remote-SSH: Connect to Host"
   - Enter: `pi@<PI_IP_ADDRESS>`
   - Open folder: `/home/pi/speakerDallama`

### Transfer Files to Pi:

**Option A: Using `scp`**:
```bash
# Copy entire project directory
scp -r /home/jim/development/speakerDallama pi@<PI_IP_ADDRESS>:~/

# Or use rsync (better for updates):
rsync -avz --exclude '__pycache__' --exclude '*.pyc' \
  /home/jim/development/speakerDallama/ \
  pi@<PI_IP_ADDRESS>:~/speakerDallama/
```

**Option B: Using Git** (recommended):
```bash
# On your dev machine, initialize git repo:
cd /home/jim/development/speakerDallama
git init
git add .
git commit -m "Initial commit"

# On Pi:
cd ~
git clone <your-repo-url>
# Or if using local network, set up git server or use USB drive
```

**Option C: Using VS Code Remote**:
- Just open the remote folder - files sync automatically

---

## Option 2: Samba (File Sharing)

Samba lets you access Pi files as a network drive.

### On Raspberry Pi 3:

1. **Install Samba**:
   ```bash
   sudo apt-get update
   sudo apt-get install samba samba-common-bin
   ```

2. **Configure Samba**:
   ```bash
   sudo nano /etc/samba/smb.conf
   ```
   
   Add at the end:
   ```
   [speakerDallama]
   path = /home/pi/speakerDallama
   valid users = pi
   read only = no
   browsable = yes
   ```

3. **Set Samba password**:
   ```bash
   sudo smbpasswd -a pi
   ```

4. **Restart Samba**:
   ```bash
   sudo systemctl restart smbd
   sudo systemctl enable smbd
   ```

### On Your Development Machine:

1. **Connect to Samba share**:
   - **Linux**: `smb://<PI_IP_ADDRESS>/speakerDallama` in file manager
   - **Windows**: `\\<PI_IP_ADDRESS>\speakerDallama` in Explorer
   - **Mac**: `smb://<PI_IP_ADDRESS>/speakerDallama` in Finder

2. **Mount permanently** (Linux):
   ```bash
   sudo mkdir /mnt/pi
   sudo mount -t cifs //<PI_IP_ADDRESS>/speakerDallama /mnt/pi \
     -o username=pi,password=<samba_password>,uid=$(id -u),gid=$(id -g)
   ```

---

## Option 3: SFTP (File Transfer Only)

If you just need file transfer without full remote access:

**Using FileZilla or similar**:
- Host: `sftp://<PI_IP_ADDRESS>`
- Username: `pi`
- Password: your Pi password
- Port: 22

---

## Recommended Workflow

1. **Set up SSH** (most important)
2. **Use VS Code/Cursor Remote SSH** for editing
3. **Use Git** for version control and syncing
4. **Test directly on Pi** via SSH terminal

### Quick Setup Script for Pi

Create this on your Pi (`~/setup_dev.sh`):

```bash
#!/bin/bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install development tools
sudo apt-get install -y \
  python3-pip \
  python3-venv \
  git \
  portaudio19-dev \
  python3-pyaudio \
  vim \
  nano

# Enable SSH if not already
sudo systemctl enable ssh
sudo systemctl start ssh

# Create project directory
mkdir -p ~/speakerDallama
cd ~/speakerDallama

echo "Setup complete! Ready for development."
```

Run with: `chmod +x ~/setup_dev.sh && ~/setup_dev.sh`

---

## Security Notes

1. **Change default password**: `passwd`
2. **Disable password login** (use keys only):
   ```bash
   sudo nano /etc/ssh/sshd_config
   # Set: PasswordAuthentication no
   sudo systemctl restart ssh
   ```
3. **Use firewall** (optional):
   ```bash
   sudo apt-get install ufw
   sudo ufw allow ssh
   sudo ufw enable
   ```

---

## Troubleshooting

**Can't connect via SSH?**
- Check Pi is on same network
- Verify SSH is running: `sudo systemctl status ssh`
- Check firewall: `sudo ufw status`

**Permission denied?**
- Check SSH key is copied: `ssh-copy-id pi@<PI_IP_ADDRESS>`
- Verify permissions: `chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys`

**Samba not accessible?**
- Check Samba is running: `sudo systemctl status smbd`
- Verify firewall allows Samba: `sudo ufw allow samba`
- Test locally: `smbclient -L localhost -U pi`



