#!/usr/bin/env python3
import os
import datetime
import subprocess
import argparse
import sys
import logging

# --- Configuration ---
# Directory where restore points will be stored.
# This should be a location accessible by root and ideally on a separate partition
# or a location not frequently modified by regular operations.
RESTORE_BASE_DIR = "/var/backups/linux_restore_points"

# --- Custom Colored Log Formatter ---
class ColoredFormatter(logging.Formatter):
    """
    A custom logging formatter that adds ANSI escape codes for colored output
    based on the log level.
    """
    GREEN = "\033[92m"   # For specific success messages
    YELLOW = "\033[93m"  # For WARNING
    RED = "\033[91m"     # For ERROR and CRITICAL
    RESET = "\033[0m"    # Resets color to default
    BOLD = "\033[1m"     # Bold text

    # Define the base format string
    FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

    # Map log levels to colored format strings
    # INFO messages are uncolored by default now, except for explicit prints
    FORMATS = {
        logging.INFO: FORMAT,
        logging.WARNING: YELLOW + FORMAT + RESET,
        logging.ERROR: RED + FORMAT + RESET,
        logging.CRITICAL: BOLD + RED + FORMAT + RESET,
        logging.DEBUG: FORMAT
    }

    def format(self, record):
        """
        Applies the appropriate colored format based on the log record's level.
        """
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

# --- Logging Setup Function ---
def configure_per_process_logging(action_name, timestamp):
    """
    Configures logging for a specific process, creating a unique log file.
    Removes existing handlers to prevent duplicate output.
    """
    log_file_name = f"linux_restore_point_{action_name}_{timestamp}.log" # Updated log file name
    process_log_file_path = os.path.join(RESTORE_BASE_DIR, log_file_name)

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO) # Ensure base level is INFO

    # Remove existing handlers to avoid duplicate logs if called multiple times
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close() # Close the file handler to release the file

    # Create new handlers for this process
    file_handler = logging.FileHandler(process_log_file_path)
    stream_handler = logging.StreamHandler(sys.stdout)

    # Set formatters
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    stream_handler.setFormatter(ColoredFormatter()) # Use custom colored formatter for console

    # Add handlers to the root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

    # Explicitly flush the stream handler to ensure immediate output
    stream_handler.flush()

    logging.info(f"Logging to: {process_log_file_path}")
    return process_log_file_path

# --- Helper Functions ---

def run_command(command, check_sudo=False, capture_output=True):
    """
    Executes a shell command and handles errors.
    If check_sudo is True, it will verify if the script is run with root privileges.
    """
    if check_sudo and os.geteuid() != 0:
        logging.error("Error: This operation requires root privileges. Please run with 'sudo'.")
        sys.exit(1)
    try:
        result = subprocess.run(command, shell=True, check=True,
                                capture_output=capture_output, text=True)

        if capture_output and result.stderr:
            logging.warning(f"Command '{command}' produced stderr: {result.stderr.strip()}")

        return result.stdout.strip() if capture_output else None
    except subprocess.CalledProcessError as e:
        logging.error(f"Error executing command: {command}")
        logging.error(f"Return Code: {e.returncode}")
        logging.error(f"STDOUT: {e.stdout.strip()}")
        logging.error(f"STDERR: {e.stderr.strip()}")
        if "Permission denied" in e.stderr:
            logging.error("This might be a permission issue even with sudo. Check directory permissions.")
        sys.exit(1)
    except FileNotFoundError:
        logging.error(f"Error: Command not found. Make sure '{command.split(' ')[0]}' is in your PATH.")
        sys.exit(1)
    except PermissionError:
        logging.error(f"Permission denied when trying to execute: {command}")
        logging.error("Ensure you have the necessary permissions, even with sudo.")
        sys.exit(1)

def ensure_restore_dir():
    """Ensures the base directory for restore points exists."""
    if not os.path.exists(RESTORE_BASE_DIR):
        print(f"Creating restore point directory: {RESTORE_BASE_DIR}")
        run_command(f"mkdir -p {RESTORE_BASE_DIR}", check_sudo=True)
        run_command(f"chmod 700 {RESTORE_BASE_DIR}", check_sudo=True)

# Ensure the base directory exists before any logging or operations
try:
    ensure_restore_dir()
except SystemExit:
    print("Failed to initialize restore directory. Exiting.")
    sys.exit(1)

def check_pv_installed():
    """Checks if 'pv' (Pipe Viewer) is installed for progress indication."""
    try:
        subprocess.run("pv --version", shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logging.warning("'pv' (Pipe Viewer) not found. Progress bar will not be displayed.")
        logging.warning("To enable progress, please install it (e.g., 'sudo apt install pv' or 'sudo yum install pv').")
        return False

def get_mounted_usb_drives():
    """
    Detects and returns a list of mounted USB drive paths.
    Uses lsblk to identify USB devices and their mount points.
    """
    usb_mount_points = []
    try:
        lsblk_output = subprocess.run(
            "lsblk -o NAME,MOUNTPOINT,TYPE,TRAN,FSTYPE -nr",
            shell=True, check=True, capture_output=True, text=True
        ).stdout.strip().split('\n')

        for line in lsblk_output:
            parts = line.split()
            if len(parts) < 2:
                continue

            name = parts[0]
            mountpoint = parts[1] if parts[1] != "(null)" else None
            dev_type = parts[2]
            transport = parts[3] if len(parts) > 3 else ''
            fstype = parts[4] if len(parts) > 4 else ''

            if mountpoint and mountpoint.startswith('/') and dev_type == 'part' and 'usb' in transport.lower():
                if not mountpoint.startswith(('/boot', '/var', '/usr', '/opt', '/lib', '/etc', '/bin', '/sbin', '/root')):
                    usb_mount_points.append(mountpoint)
            elif mountpoint and mountpoint.startswith('/') and dev_type == 'disk' and 'usb' in transport.lower():
                 if not mountpoint.startswith(('/boot', '/var', '/usr', '/opt', '/lib', '/etc', '/bin', '/sbin', '/root')):
                    usb_mount_points.append(mountpoint)

    except Exception as e:
        logging.warning(f"Could not detect USB drives using lsblk: {e}")
        return []

    unique_mount_points = sorted(list(set(usb_mount_points)))
    valid_mount_points = [mp for mp in unique_mount_points if os.path.isdir(mp)]

    return valid_mount_points

# --- Main Operations ---

def create_restore_point(name, backup_type, include_usb):
    """
    Creates a new restore point.
    A restore point is a compressed tar archive of the specified system directories.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    current_log_file = configure_per_process_logging("create", timestamp)

    restore_point_name = f"{name}_{timestamp}" if name else f"restore_{timestamp}"
    archive_path = os.path.join(RESTORE_BASE_DIR, f"{restore_point_name}.tar.gz")

    backup_targets = []
    if backup_type == "system":
        backup_targets = ["/etc"]
        logging.info("Creating a system-only restore point (backing up /etc).")
    elif backup_type == "full":
        backup_targets = ["/etc", "/home"]
        logging.info("Creating a full system restore point (backing up /etc and /home).")
    else:
        logging.error(f"Invalid backup type specified: {backup_type}. Must be 'system' or 'full'.")
        sys.exit(1)

    if include_usb:
        usb_drives = get_mounted_usb_drives()
        if not usb_drives:
            logging.info("No mounted USB drives detected to include.")
        else:
            logging.info("Detected mounted USB drives:")
            for i, usb_path in enumerate(usb_drives):
                print(f"  {i+1}. {usb_path}")
            print("Enter the numbers of USB drives to include (e.g., '1,3' or 'all'): ", end="")
            selection = input().strip().lower()

            selected_usb_paths = []
            if selection == "all":
                selected_usb_paths = usb_drives
            else:
                try:
                    indices = [int(x.strip()) - 1 for x in selection.split(',') if x.strip()]
                    for idx in indices:
                        if 0 <= idx < len(usb_drives):
                            selected_usb_paths.append(usb_drives[idx])
                        else:
                            logging.warning(f"Invalid selection: {idx+1}. Skipping.")
                except ValueError:
                    logging.error("Invalid input for USB selection. Skipping USB inclusion.")

            if selected_usb_paths:
                backup_targets.extend(selected_usb_paths)
                logging.info(f"Including selected USB drives: {', '.join(selected_usb_paths)}")
            else:
                logging.info("No USB drives selected or validly entered.")

    exclude_paths = [
        "/proc", "/sys", "/dev", "/run", "/tmp", "/mnt", "/media",
        os.path.join(RESTORE_BASE_DIR, "*")
    ]

    tar_command_parts = [
        "tar", "-c", "-P", "--absolute-names"
    ]
    for ex in exclude_paths:
        tar_command_parts.append(f"--exclude={ex}")
    tar_command_parts.extend(backup_targets)
    tar_command_parts.append("-f -")

    total_size_bytes = 0
    for target in backup_targets:
        try:
            temp_exclude_file = None
            if exclude_paths:
                temp_exclude_file = os.path.join("/tmp", f"tar_excludes_{os.getpid()}.txt")
                with open(temp_exclude_file, "w") as f:
                    for ex in exclude_paths:
                        f.write(f"{ex}\n")
                du_command = f"sudo du -sb --exclude-from={temp_exclude_file} {target}"
            else:
                du_command = f"sudo du -sb {target}"

            size_output = subprocess.run(du_command, shell=True, check=True,
                                         capture_output=True, text=True).stdout.strip()
            total_size_bytes += int(size_output.split('\t')[0])
        except (subprocess.CalledProcessError, ValueError) as e:
            logging.warning(f"Could not get size for {target}: {e}. Progress bar might be inaccurate.")
            total_size_bytes = 0
        finally:
            if temp_exclude_file and os.path.exists(temp_exclude_file):
                os.remove(temp_exclude_file)

    pv_installed = check_pv_installed()
    progress_command = ""
    if pv_installed and total_size_bytes > 0:
        progress_command = f"| pv -p -s {total_size_bytes} -N 'Archiving' | gzip > {archive_path}"
    else:
        progress_command = f"| gzip > {archive_path}"

    full_command = f"sudo {' '.join(tar_command_parts)} {progress_command}"

    logging.info(f"Creating restore point '{restore_point_name}'...")
    logging.info(f"Backing up: {', '.join(backup_targets)}")
    logging.info(f"Saving to: {archive_path}")

    run_command(full_command, check_sudo=True, capture_output=False)
    print(f"{ColoredFormatter.GREEN}Restore point '{restore_point_name}' created successfully!{ColoredFormatter.RESET}")
    logging.info(f"Process log file: {current_log_file}")


def list_restore_points():
    """Lists all available restore points."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    current_log_file = configure_per_process_logging("list", timestamp) # Reconfigure logging for list command

    restore_points = []
    # Check if the directory exists and is readable before listing
    if os.path.exists(RESTORE_BASE_DIR):
        try:
            for item in os.listdir(RESTORE_BASE_DIR):
                if item.endswith(".tar.gz"):
                    restore_points.append(item.replace('.tar.gz', ''))
        except PermissionError:
            logging.error(f"Permission denied when listing directory: {RESTORE_BASE_DIR}. Ensure you have root privileges.")
            logging.info(f"Process log file: {current_log_file}")
            return

    if not restore_points:
        print(f"{ColoredFormatter.YELLOW}No restore points found.{ColoredFormatter.RESET}") # Changed to yellow for clarity
        logging.info(f"Process log file: {current_log_file}") # Log the file for empty list too
        return

    print(f"{ColoredFormatter.GREEN}Available Restore Points:{ColoredFormatter.RESET}")
    for rp in sorted(restore_points):
        print(f"{ColoredFormatter.GREEN}- {rp}{ColoredFormatter.RESET}")
    logging.info(f"Process log file: {current_log_file}")


def restore_from_point(name):
    """
    Restores the system from a specified restore point.
    WARNING: This will overwrite existing files in the backed-up directories.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    current_log_file = configure_per_process_logging("restore", timestamp)

    archive_path = os.path.join(RESTORE_BASE_DIR, f"{name}.tar.gz")

    if not os.path.exists(archive_path):
        logging.error(f"Error: Restore point '{name}' not found at {archive_path}")
        list_restore_points()
        sys.exit(1)

    logging.warning(f"WARNING: Restoring from '{name}'. This will overwrite existing files on your system.")
    logging.warning("It is highly recommended to reboot into a live environment (e.g., a USB stick) before restoring.")
    logging.warning("Proceeding without a live environment might lead to an unstable system or data corruption.")
    print("Are you absolutely sure you want to proceed? (type 'yes' to confirm): ", end="")
    confirmation = input().strip().lower()

    if confirmation != "yes":
        logging.info("Restoration cancelled by user.")
        return

    logging.info(f"Restoring from '{name}'...")

    pv_installed = check_pv_installed()
    progress_command = ""
    if pv_installed:
        archive_size = os.path.getsize(archive_path)
        progress_command = f"pv -p -s {archive_size} -N 'Extracting' {archive_path} | "
    else:
        progress_command = f"cat {archive_path} | "

    restore_command = f"{progress_command} tar -xzP --absolute-names -C /"

    run_command(restore_command, check_sudo=True, capture_output=False)
    print(f"{ColoredFormatter.GREEN}Restoration from '{name}' completed successfully!{ColoredFormatter.RESET}")
    logging.info(f"Process log file: {current_log_file}")

def delete_restore_point(name):
    """
    Deletes a specified restore point.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    current_log_file = configure_per_process_logging("delete", timestamp)

    archive_path = os.path.join(RESTORE_BASE_DIR, f"{name}.tar.gz")

    if not os.path.exists(archive_path):
        logging.error(f"Error: Restore point '{name}' not found at {archive_path}")
        list_restore_points()
        sys.exit(1)

    logging.warning(f"WARNING: You are about to delete the restore point '{name}'. This action cannot be undone.")
    print("Are you absolutely sure you want to delete this restore point? (type 'yes' to confirm): ", end="")
    confirmation = input().strip().lower()

    if confirmation != "yes":
        logging.info("Deletion cancelled by user.")
        return

    try:
        os.remove(archive_path)
        print(f"{ColoredFormatter.GREEN}Restore point '{name}' deleted successfully!{ColoredFormatter.RESET}")
    except OSError as e:
        logging.error(f"Error deleting restore point '{name}': {e}")
        logging.error("Ensure you have the necessary permissions. Run with 'sudo'.")
        sys.exit(1)
    logging.info(f"Process log file: {current_log_file}")

# --- Command Line Interface ---

def main():
    parser = argparse.ArgumentParser(
        description="Linux Restore Point Tool - Create and restore system configuration snapshots.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "action",
        choices=["create", "list", "restore", "delete"],
        help="""
        create: Create a new restore point.
        list:   List all available restore points.
        restore: Restore the system from a specific restore point.
        delete: Delete a specific restore point.
        """
    )
    parser.add_argument(
        "-n", "--name",
        help="Name for the restore point (for 'create', 'restore', and 'delete' actions)."
    )
    parser.add_argument(
        "-t", "--type",
        choices=["system", "full"],
        default="system",
        help="""
        Type of restore point to create (for 'create' action only):
        system: Backs up /etc (system configuration files). (default)
        full:   Backs up /etc and /home (system and user data).
        """
    )
    parser.add_argument(
        "--include-usb",
        action="store_true",
        help="""
        For 'create' action: Detects and allows selection of mounted USB drives
        to include in the restore point.
        """
    )

    args = parser.parse_args()

    # The initial ensure_restore_dir() is called globally for safety.
    # Logging for specific actions will be configured within their respective functions.

    if args.action == "create":
        create_restore_point(args.name, args.type, args.include_usb)
    elif args.action == "list":
        list_restore_points()
    elif args.action == "restore":
        if not args.name:
            logging.error("Error: --name is required for 'restore' action.")
            list_restore_points()
            sys.exit(1)
        restore_from_point(args.name)
    elif args.action == "delete":
        if not args.name:
            logging.error("Error: --name is required for 'delete' action.")
            list_restore_points()
            sys.exit(1)
        delete_restore_point(args.name)

if __name__ == "__main__":
    main()
