# **Linux Restore Tool 💾**

A powerful command-line tool for Linux that brings Windows-like restore point functionality to your system. Easily create snapshots of your critical system configurations and user data, and revert to them when you need to.

## **✨ Features**

* **Flexible Restore Points:**  
  * **System-only:** Backup just your /etc directory (system configuration files).  
  * **Full System:** Include both /etc and your /home directory (user data) for a complete snapshot.  
* **USB Drive Inclusion:** Optionally include mounted USB drives in your backups. The tool will detect them and let you choose which ones to add.  
* **Seamless Restoration:** Restore your system from any previously created restore point.  
* **Easy Cleanup:** Delete old or unwanted restore points to save disk space.  
* **Real-time Progress:** Get visual feedback with a dynamic progress bar during backup and restore operations, powered by pv (Pipe Viewer).  
* **Comprehensive Logging:** Every create, restore, and delete action generates its own detailed log file, perfect for reviewing operations or troubleshooting.  
* **Colored Output:** Enjoy clear, at-a-glance status updates in your terminal:  
  * **Green:** Successful operations.  
  * **Yellow:** Warnings.  
  * **Red:** Errors.

## **🚀 Installation**

### **System Dependencies**

Before installing the tool, make sure you have pv (Pipe Viewer) and tar installed on your Linux distribution.

* **For Debian/Ubuntu/Kali:**  
```bash
  sudo apt update  
  sudo apt install pv tar
```
* **For Fedora/RHEL/CentOS:**  
```bash
  sudo dnf install pv tar
```
* **For Arch Linux:**  
```bash
  sudo pacman \-S pv tar
```
### **Install the Tool**

Due to Python's "externally-managed-environment" policy (PEP 668\) on many modern Linux distributions, direct pip install . might be prevented to protect system integrity. Here are the recommended ways to install your tool:

#### **Using pipx (Recommended for Command-Line Applications)**

pipx installs Python applications into isolated environments and makes them available globally. It's the easiest way to manage CLI tools.

1. **Install pipx** (if you don't have it):  
  * For Debian / Ubuntu / Kali:
```bash
   sudo apt install pipx   
```
  * OR if pipx is not in your distro's repos (less common for Kali):
```bash  
   python3 \-m pip install \--user pipx --break-system-packages  
   python3 \-m pipx ensurepath
```
2. Add pipx path to the secure path to be able to run it with `sudo`:
  
  * Find the pipx path:

```bash
pipx environment
```
  * You should see something like this:
```BASH
  Environment variables (set by user):

  PIPX_HOME=
  PIPX_GLOBAL_HOME=
  PIPX_BIN_DIR=
  PIPX_GLOBAL_BIN_DIR=
  PIPX_MAN_DIR=
  PIPX_GLOBAL_MAN_DIR=
  PIPX_SHARED_LIBS=
  PIPX_DEFAULT_PYTHON=
  PIPX_FETCH_MISSING_PYTHON=
  USE_EMOJI=
  PIPX_HOME_ALLOW_SPACE=

  Derived values (computed by pipx):

  PIPX_HOME=/home/YOUR_USERNAME/.local/share/pipx
  PIPX_BIN_DIR=/home/YOUR_USERNAME/.local/bin # <--- Copy the `BIN` path
  PIPX_MAN_DIR=/home/YOUR_USERNAME/.local/share/man
  PIPX_SHARED_LIBS=/home/YOUR_USERNAME/.local/share/pipx/shared
  PIPX_LOCAL_VENVS=/home/YOUR_USERNAME/.local/share/pipx/venvs
  PIPX_LOG_DIR=/home/YOUR_USERNAME/.local/state/pipx/log
  PIPX_TRASH_DIR=/home/YOUR_USERNAME/.local/share/pipx/trash
  PIPX_VENV_CACHEDIR=/home/YOUR_USERNAME/.cache/pipx
  PIPX_STANDALONE_PYTHON_CACHEDIR=/home/YOUR_USERNAME/.local/share/pipx/py
  PIPX_DEFAULT_PYTHON=/usr/bin/python3.13
  USE_EMOJI=true
  PIPX_HOME_ALLOW_SPACE=false
```
  * Copy the `BIN` path

3. **Open sudoers with visudo:**  
```bash
sudo visudo
```
  * look for a line like this:
  `Defaults        secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`
  * Add the copied `pipx BIN` path to is so it will be look like this:
  `Defaults        secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:<path/to/pipx/bin/path>`

  - example
  `Defaults        secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/home/YOUR_USERNAME/.local/bin`

  * **Save and Exit visudo:**  
     * If using vi (default for visudo): Press Esc, then type :wq and press Enter.  
    * If using nano (if configured): Press Ctrl+X, then Y to confirm save, then Enter.  
  * **Open a new terminal session** for the changes to take effect.

4. **Navigate to your project directory:**  
```bash
   cd /path/to/your/linux-restore-point
```

5. **Install your tool with pipx:**  
```bash   
   pipx install .
```
   This will install linux-restore-point in its own isolated environment and make the linux-restore-point command globally available for your user.

## **💡 Usage**

All operations of linux-restore-point require sudo privileges as they interact with system-level directories and files.



Now you can use the commands directly:

* **Example of Creating a restore point:**  
```bash
  sudo linux-restore-point create -n <name_of_backup> -t [system|full]
```

  - `full` the entire system with user data.
  - `system` only the system no user data.

 > * \-n \<name\_of\_backup\>: A custom, descriptive name for your restore point (e.g., pre\_kernel\_update). A timestamp will be automatically appended.  
 > * \-t system: (Default) Backs up only /etc (your system's configuration files).  
 > * \-t full: Backs up both /etc and /home (your system configuration and all user data).  
 > * \--include-usb: (Optional flag) If present, the tool will detect and prompt you to select any currently mounted USB drives to include in the backup.
* **Example of listing restore points**
```bash
sudo linux-restore-point list
```
  - out put will look like:
```bash
Available Restore Points:
- mysecondbackup_20250804_212105
```

* **Example of Restoring a restore point**
```bash
sudo linux-restore-point restore -n <Restore_point_name>
```

  * \<full\_restore\_point\_name\>: The **exact** name of the restore point as shown by linux-restore-point list (e.g., pre\_big\_software\_install\_20250804\_194115).  
  * **⚠️ WARNING:** Restoring will **overwrite** existing files in the backed-up locations. It is **highly recommended** to perform a restore from a **live Linux environment** (e.g., booting from a USB stick with your Linux distribution) to prevent issues with files being in use and to ensure system stability.


* **Delete a restore point:** 
```bash 
  sudo linux-restore-point delete -n <full_restore_point_name\>
```
  * \<full\_restore\_point\_name\>: The exact name of the restore point to delete.  
  * **⚠️ WARNING:** This action is **irreversible**. Once a restore point is deleted, it cannot be recovered.


### **Alternative: Using sudo env PATH="$PATH" (No sudoers modification)**

If you prefer not to modify sudoers, you can always use the more verbose command:
```bash
sudo env PATH="$PATH" linux-restore-point \<action\> \[options\]
```

## **📄 Logging**

Every create, restore, and delete operation generates its own unique log file. These are stored in /var/backups/linux\_restore\_points/ and named like linux\_restore\_point\_\<action\>\_\<timestamp\>.log. These logs provide detailed information about the process, including any warnings or errors encountered.

## **🤝 Contributing**

Contributions are welcome\! Feel free to fork the repository, make improvements, and submit pull requests.

## **📜 License**

This project is licensed under the MIT License. See the LICENSE file for full details.