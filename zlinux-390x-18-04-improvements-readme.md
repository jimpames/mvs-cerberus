# zLinux Improvements - Ubuntu 18.04 s390x on Hercules/Hyperion

**Modern Development Environment on Ancient Base**

## Overview

This document describes the modernization enhancements added to the original zLinux installer for **Ubuntu 18.04 on s390x** (running under Hercules/Hyperion).

The original installer provided a very outdated base system (Python 3.6, ancient GCC, no modern Go, etc.). These improvements allow you to have a **productive modern development stack** without upgrading past Ubuntu 18.04 (which would break Hercules compatibility).

## Key Improvements

### 1. Automated Modern Toolchain Installation
- **Go** 1.23.4 (official Google linux-s390x binary)
- **Python** 3.10 (via Deadsnakes PPA) with full development support
- **Flask**, FastAPI, Gunicorn, Uvicorn, and other popular Python packages
- Comprehensive build tools and libraries

### 2. Fully Automated Post-Install Process
- The modernization runs automatically during the Ubuntu installation via **preseed late_command**
- No manual intervention needed after the initial install
- Detailed log written to `/var/log/modern_bootstrap.log`

### 3. Enhanced Development Environment
- Full `build-essential`, CMake, Ninja, Git, curl, etc.
- SSL, compression, XML, and other development libraries
- Proper Python virtualenv and pip support
- Go environment configured system-wide

### 4. Improved Installer Integration
- Updated `config_preseed` script to inject both preseed.cfg and the modern post-install script into the initrd
- New `templates/post_install_modern.sh` script
- Clean separation of concerns

## Files Added / Modified

| File | Purpose |
|------|--------|
| `templates/post_install_modern.sh` | Main script that installs Go, Python 3.10, Flask, etc. |
| `config_preseed` | Now copies the modern script into initrd and adds late_command |
| `zlinux_improvements_18-04-s390x-readme.md` | This documentation |

## How to Use

1. Place the two new files in the correct locations (as provided).
2. Run the main installer:
   ```bash
   ./zlinux_install.bash
   
   After installation completes and you boot the system, the modernization will run automatically.
Log in as zubuntu and check status:Bashcat /var/log/modern_bootstrap.log
Verify tools:Bashgo version
python3 --version
python3 -c "import flask; print('Flask is ready')"

Post-Installation Commands
Bash# Enable Go in current shell
source /etc/profile.d/go.sh

# Create a Python virtual environment
python3 -m venv myproject
source myproject/bin/activate
pip install -r requirements.txt
Updating Tools Later

Go: Download newer version from https://go.dev/dl/ and replace /usr/local/go
Python packages: Use pip install --upgrade
System updates: apt-get update && apt-get upgrade -y

Important Notes

Ubuntu 18.04 is EOL (End of Life). Use this environment for development/testing only.
Security updates are limited. Consider running behind a firewall.
The Deadsnakes PPA is used for Python 3.10 — it is still functional on Bionic.
Hercules performance is slow for heavy compilation — prefer Go binaries when possible.

Future Enhancements (Optional)

Rust via rustup
Node.js via nvm
Additional language runtimes
SSH key injection
Automatic service setup


Maintained as part of the zLinux modernization project.
Last updated: May 2026