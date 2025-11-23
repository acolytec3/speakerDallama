# Installing pip3 on Raspberry Pi

**Note:** Consider using `uv` instead - it's much faster! See [INSTALL_UV.md](INSTALL_UV.md)

If `pip3` is not installed, here's how to install it:

## Quick Install

```bash
# Update package list
sudo apt-get update

# Install pip3
sudo apt-get install -y python3-pip

# Verify installation
pip3 --version
```

## Alternative: Install using get-pip.py

If the package manager method doesn't work:

```bash
# Download get-pip.py
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py

# Install pip3
python3 get-pip.py --user

# Add to PATH (if needed)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Verify
pip3 --version
```

## After Installing pip3

Once pip3 is installed, you can:

1. Install project dependencies:
   ```bash
   pip3 install --user -r requirements.txt
   ```

2. Or install individually:
   ```bash
   pip3 install --user vosk pyaudio pyyaml numpy
   ```

## Troubleshooting

**"pip3: command not found" after installation:**
- Try: `python3 -m pip --version`
- If that works, use `python3 -m pip` instead of `pip3`

**Permission errors:**
- Use `--user` flag: `pip3 install --user <package>`
- Or use virtual environment: `python3 -m venv venv && source venv/bin/activate`

