# Linux Restore Point

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)]()
[![GitHub Release](https://img.shields.io/github/v/release/Myusername/linux-restore-point)]()

A command-line utility for creating and restoring Linux system restore points.

## Features
- Create system-only (`/etc`) or full-system (`/etc` + `/home`) backups
- Optional USB drive inclusion with interactive selection
- Real-time progress tracking with `pv` (Pipe Viewer)
- Color-coded console output for better user experience
- Comprehensive logging with timestamped operation logs
- Restore point management (list/delete)
- Robust error handling and safety confirmations
- Proper Python packaging for easy installation

## Installation

### 1. Install Dependencies
```bash
sudo apt update
sudo apt install tar pv
```
### 2. Install Python Package Manager (pipx)
```bash
sudo apt install pipx  # Debian/Ubuntu/Kali
# OR
python3 -m pip install --user pipx

# Ensure pipx is in your PATH
python3 -m pipx ensurepath
```
### 3. Install Linux Restore Point
```bash
pipx install linux-restore-point
```
### 4. Enable Sudo Access
- To run the tool with sudo, you need to make it accessible in sudo's PATH:
```bash
# Temporary solution (per session):
sudo env PATH="$PATH" linux-restore-point [command]

# Permanent solution (add pipx bin to secure_path):
sudo visudo
```
- Add the pipx binary path to secure_path (find your path with `pipx environments` ):
```bash
Defaults secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/home/youruser/.local/bin"
```
Save and exit (Ctrl+X, then Y to confirm).

#### Usage
##### Create a Restore Point
```bash
# System-only backup (only /etc directory)
sudo linux-restore-point create --type system

# Full system backup (includes /etc and /home)
sudo linux-restore-point create --type full

# Include USB drives in backup (interactive selection)
sudo linux-restore-point create --type full --include-usb
```
##### List Available Restore Points
```bash
sudo linux-restore-point list
```
###### Example output:
```
Name                      Type       Date             Size (MB)
---------------------------------------------------------------
full_20230805_1430        full       2023-08-05 14:30   1024.50
system_20230804_0930      system     2023-08-04 09:30     85.75
```
###### Restore from a Point
```bash
# Restore with confirmation prompt
sudo linux-restore-point restore full_20230805_1430

# Force restore (skip confirmation - DANGEROUS!)
sudo linux-restore-point restore system_20230804_0930 --force
```
##### Delete a Restore Point
```bash
# Delete with confirmation
sudo linux-restore-point delete full_20230805_1430

# Force delete (skip confirmation)
sudo linux-restore-point delete system_20230804_0930 --force
```
#### Advanced Installation Options
##### Install from GitHub
```bash
pipx install git+https://github.com/Myusername/linux-restore-point.git

# Install specific version
pipx install git+https://github.com/Myusername/linux-restore-point.git@v1.0.0
```
##### Install for Development
```bash
git clone https://github.com/Myusername/linux-restore-point.git
cd linux-restore-point
pipx install .
```
##### Logging
- All operations generate detailed log files stored in:
`/var/backups/linux_restore_points/logs/`
- Log files follow the naming convention:

* ` linux_restore_point_create_YYYYMMDD_HHMMSS.log`

*  `linux_restore_point_restore_YYYYMMDD_HHMMSS.log`

*  `linux_restore_point_delete_YYYYMMDD_HHMMSS.log`

###### Each log contains:
* Timestamps for all operations

* Command execution details

* Error messages with tracebacks

* Operation metadata

##### Safety Notes 
1. Restore Operations Are Destructive:
    
    * Restoration will overwrite existing files
    * Always verify you have current backups
    * Recommended to restore from a live environment

2. Full Backups Include Home Directories:
    
    * Be mindful of disk space

    * Consider excluding large media files

3. USB Drive Handling:

    * Only includes mounted USB drives.

    * Requires user interaction to select drives.

    * Does not backup unmounted or raw devices.


#### Uninstallation
```bash
# Uninstall Python package
pipx uninstall linux-restore-point

# Remove backup data (WARNING: deletes all restore points!)
sudo rm -rf /var/backups/linux_restore_points
```

##### Troubleshooting
###### "Command not found" after installation
```bash
# Reload your shell
exec bash

# Or manually add pipx to PATH
export PATH="$HOME/.local/bin:$PATH"
```

###### Permission Errors
```bash
# Ensure restore directory exists
sudo mkdir -p /var/backups/linux_restore_points
sudo chmod 700 /var/backups/linux_restore_points
```

###### PV Progress Bar Not Showing
```bash
# Verify pv is installed
sudo apt install pv

# Test pv functionality
echo "Test" | pv | cat
```

#### Contributing
 ###### Contributions are welcome! Here's how to contribute:

1. Fork the repository.
2. Create a new branch (git checkout -b feature/your-feature).
3. Commit your changes (git commit -am 'Add some feature').
4. Push to the branch (git push origin feature/your-feature).
5. Create a new Pull Request.

##### Development Setup
```bash
git clone https://github.com/Myusername/linux-restore-point.git
cd linux-restore-point
python3 -m venv venv
source venv/bin/activate
pip install -e .
```
##### Testing Guidelines

*  Include tests for new features

*  Maintain PEP 8 compliance

*  Use descriptive commit messages

*  Update documentation when adding features

##### License
  - This project is licensed under the MIT License - see the [LICENSE](https://github.com/OmarBjjash/linux-restore-point/blob/main/LICENSE) file for details.

##### Disclaimer

    - This tool comes with NO WARRANTY. Use at your own risk. The authors are not responsible for any data loss or system damage caused by improper use of this software. Always maintain separate backups of critical data.

### Important Notes:
>1. **Replace Placeholders**:
>   - Replace `Myusername` with your actual GitHub username
>   - Replace `youruser` in the secure_path with your actual username 
   >

>2. **To Use**:
>   - Copy this entire code block
>  - Paste it into your `README.md` file
>   - Save the file
>
>3. **Formatting**:
>   - The markdown is properly formatted with headers, code blocks, and sections
>   - All code examples are in separate code blocks with language identifiers
>   - Badges will automatically work when uploaded to GitHub
>
>>This README contains all the necessary documentation for your Linux Restore Point tool and will render correctly on GitHub.
>>