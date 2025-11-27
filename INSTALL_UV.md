# Installing uv on Raspberry Pi

`uv` is a fast Python package installer written in Rust. It's much faster than pip and has better dependency resolution.

## Quick Install

```bash
# Install uv (one command)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH for current session
export PATH="$HOME/.cargo/bin:$PATH"

# Or add to ~/.bashrc for permanent access
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Verify installation
uv --version
```

## Using uv Instead of pip

### Basic Usage

```bash
# Install packages (creates venv automatically if needed)
uv pip install vosk pyaudio pyyaml numpy

# Or install from requirements.txt
uv pip install -r requirements.txt

# Create virtual environment explicitly
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Advantages of uv

- **Much faster** - 10-100x faster than pip
- **Better dependency resolution** - Handles conflicts better
- **All-in-one tool** - Replaces pip, pip-tools, virtualenv, etc.
- **Rust-based** - Fast and reliable
- **Works great on Pi** - Efficient even on slower hardware

### Migration from pip

If you're used to pip, uv commands are very similar:

| pip command | uv equivalent |
|------------|---------------|
| `pip install package` | `uv pip install package` |
| `pip install -r requirements.txt` | `uv pip install -r requirements.txt` |
| `python -m venv venv` | `uv venv` |
| `pip freeze` | `uv pip freeze` |

## Project Setup with uv

```bash
# 1. Install uv (if not already)
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"

# 2. Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# 3. Run your application
python3 main.py
```

## Troubleshooting

**"uv: command not found" after installation:**
- Check where uv is installed: `find ~ -name uv -type f 2>/dev/null`
- Common locations:
  - `~/.cargo/bin/uv` (official installer)
  - `~/.local/bin/uv` (pip install --user or some installers)
- Add to PATH based on actual location:
  ```bash
  # For ~/.cargo/bin
  export PATH="$HOME/.cargo/bin:$PATH"
  
  # For ~/.local/bin
  export PATH="$HOME/.local/bin:$PATH"
  
  # Or add both to be safe
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  ```
- Add to shell profile for permanent access:
  ```bash
  echo 'export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
  source ~/.bashrc
  ```
- Or restart your terminal session

**Installation fails:**
- Make sure you have curl installed: `sudo apt-get install curl`
- Check internet connection
- Try: `curl -LsSf https://astral.sh/uv/install.sh | sh -s -- --help`

**Permission errors:**
- uv installs to user space (`~/.cargo/bin` or `~/.local/bin`)
- No sudo needed for installation or package management

**uv disappeared after system update:**
- Check if it still exists: `ls -la ~/.local/bin/uv ~/.cargo/bin/uv`
- If it exists but isn't found, PATH issue - see above
- If it's gone, reinstall: `curl -LsSf https://astral.sh/uv/install.sh | sh`



