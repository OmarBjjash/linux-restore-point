#!/usr/bin/env python3
"""
Linux Restore Point - Create, restore, and manage system restore points
"""

import os
import sys
import argparse
import subprocess
import shutil
import logging
import time
import json
from pathlib import Path
from datetime import datetime
import re

# Constants
RESTORE_BASE_DIR = Path("/var/backups/linux_restore_points")
LOGS_DIR = RESTORE_BASE_DIR / "logs"
CONFIG_FILE = RESTORE_BASE_DIR / "config.json"
BACKUP_EXCLUDE = [
    "/dev/*", "/proc/*", "/sys/*", "/tmp/*", "/run/*", 
    "/mnt/*", "/media/*", "/lost+found", RESTORE_BASE_DIR
]

# ANSI Color Codes
COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_RED = "\033[31m"
COLOR_RESET = "\033[0m"

def setup_logger(action):
    """Set up logging with file and console handlers"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOGS_DIR / f"linux_restore_point_{action}_{timestamp}.log"
    
    logger = logging.getLogger(f"linux_restore_point_{action}")
    logger.setLevel(logging.DEBUG)
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s", 
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger, log_file

def print_color(message, color=None):
    """Print colored message to console"""
    if color == "green":
        print(COLOR_GREEN + message + COLOR_RESET)
    elif color == "yellow":
        print(COLOR_YELLOW + message + COLOR_RESET)
    elif color == "red":
        print(COLOR_RED + message + COLOR_RESET)
    else:
        print(message)

def run_command(cmd, logger, description, total_size=None):
    """Run system command with progress tracking"""
    try:
        # Use PV for progress if available
        if shutil.which("pv") and total_size:
            pv_cmd = f"pv -s {total_size}"
            cmd = f"{cmd} | {pv_cmd}"
            logger.info(f"Command with PV: {cmd}")
            process = subprocess.Popen(cmd, shell=True, executable="/bin/bash")
        else:
            logger.info(f"Command: {cmd}")
            process = subprocess.Popen(cmd, shell=True, executable="/bin/bash")
        
        process.communicate()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd)
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}", exc_info=True)
        print_color(f"Error: {description} failed - {e}", "red")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print_color(f"Unexpected error: {e}", "red")
        sys.exit(1)

def get_directory_size(path):
    """Calculate directory size in bytes"""
    try:
        result = subprocess.run(
            ["du", "-sb", path],
            capture_output=True,
            text=True,
            check=True
        )
        size = result.stdout.split()[0]
        return int(size)
    except subprocess.CalledProcessError:
        return 0

def get_mounted_usb_drives():
    """Get list of mounted USB drives"""
    usb_mounts = []
    try:
        # Get USB device identifiers
        usb_devices = []
        by_id = Path("/dev/disk/by-id")
        if by_id.exists():
            for entry in by_id.iterdir():
                if "usb-" in entry.name:
                    real_path = os.path.realpath(entry)
                    if real_path.startswith("/dev/"):
                        usb_devices.append(real_path.split("/")[-1])
        
        # Find mount points
        with open("/proc/mounts", "r") as f:
            for line in f:
                parts = line.split()
                device = parts[0].replace("/dev/", "")
                if device in usb_devices:
                    usb_mounts.append(parts[1])
    
    except Exception as e:
        print_color(f"Warning: Could not detect USB drives - {e}", "yellow")
    
    return usb_mounts

def create_restore_point(args):
    """Create system restore point"""
    # Setup environment
    os.makedirs(RESTORE_BASE_DIR, exist_ok=True, mode=0o700)
    os.makedirs(LOGS_DIR, exist_ok=True, mode=0o700)
    logger, log_file = setup_logger("create")
    
    try:
        # Determine backup type
        backup_type = "system" if args.type == "system" else "full"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{backup_type}_{timestamp}"
        backup_dir = RESTORE_BASE_DIR / backup_name
        os.makedirs(backup_dir, exist_ok=True, mode=0o700)
        
        # Build include list
        include_paths = ["/etc"]
        if backup_type == "full":
            include_paths.append("/home")
            
        # Handle USB drives
        usb_paths = []
        if args.include_usb:
            usb_mounts = get_mounted_usb_drives()
            if usb_mounts:
                print("Detected USB drives:")
                for i, path in enumerate(usb_mounts, 1):
                    print(f"{i}. {path}")
                
                selections = input(
                    "Enter USB numbers to include (comma-separated, empty to skip): "
                ).strip()
                
                if selections:
                    for sel in selections.split(","):
                        try:
                            idx = int(sel.strip()) - 1
                            if 0 <= idx < len(usb_mounts):
                                usb_paths.append(usb_mounts[idx])
                        except ValueError:
                            pass
        
        # Calculate total size
        total_size = 0
        all_paths = include_paths + usb_paths
        for path in all_paths:
            total_size += get_directory_size(path)
        
        # Build tar command
        exclude_args = " ".join([f"--exclude='{x}'" for x in BACKUP_EXCLUDE])
        include_args = " ".join(all_paths)
        backup_file = backup_dir / "backup.tar.gz"
        
        cmd = (
            f"tar --create --gzip --absolute-names "
            f"{exclude_args} "
            f"--file - {include_args} "
            f"2> {backup_dir / 'backup.log'}"
        )
        
        # Execute backup
        print(f"Creating {backup_type} restore point: {backup_name}")
        logger.info(f"Starting backup: {backup_name}")
        logger.info(f"Included paths: {all_paths}")
        
        with open(backup_file, "wb") as f:
            run_command(cmd, logger, "Backup creation", total_size)
        
        # Save metadata
        metadata = {
            "name": backup_name,
            "type": backup_type,
            "timestamp": timestamp,
            "paths": all_paths,
            "size": os.path.getsize(backup_file),
            "usb_paths": usb_paths
        }
        with open(backup_dir / "metadata.json", "w") as f:
            json.dump(metadata, f)
        
        # Report success
        logger.info(f"Backup successful: {backup_file}")
        print_color("Restore point created successfully!", "green")
        print(f"Size: {os.path.getsize(backup_file) / (1024**2):.2f} MB")
        print(f"Log file: {log_file}")
    
    except Exception as e:
        logger.error(f"Backup failed: {e}", exc_info=True)
        print_color(f"Error: Backup creation failed - {e}", "red")
        sys.exit(1)

def restore_from_point(args):
    """Restore system from a restore point"""
    # Setup environment
    os.makedirs(RESTORE_BASE_DIR, exist_ok=True, mode=0o700)
    os.makedirs(LOGS_DIR, exist_ok=True, mode=0o700)
    logger, log_file = setup_logger("restore")
    
    try:
        # Find backup
        backup_name = args.name
        backup_dir = RESTORE_BASE_DIR / backup_name
        if not backup_dir.exists():
            print_color(f"Error: Restore point '{backup_name}' not found", "red")
            sys.exit(1)
        
        # Load metadata
        with open(backup_dir / "metadata.json") as f:
            metadata = json.load(f)
        
        # Confirm restoration
        print_color("WARNING: RESTORING WILL OVERWRITE EXISTING FILES!", "yellow")
        print_color("THIS OPERATION IS DESTRUCTIVE AND CAN CAUSE DATA LOSS!", "yellow")
        print("Recommended: Perform restoration from a live environment")
        print(f"Restore point: {metadata['name']}")
        print(f"Type: {metadata['type']}")
        print(f"Date: {metadata['timestamp']}")
        print(f"Included paths: {metadata['paths']}")
        
        if not args.force:
            confirmation = input("Are you absolutely sure? (type 'YES' to confirm): ")
            if confirmation != "YES":
                print("Restoration cancelled")
                sys.exit(0)
        
        # Prepare restore command
        backup_file = backup_dir / "backup.tar.gz"
        size = os.path.getsize(backup_file)
        
        cmd = (
            f"tar --extract --gzip --absolute-names --overwrite "
            f"--file - < {backup_file} "
            f"2> {backup_dir / 'restore.log'}"
        )
        
        # Execute restoration
        print("Starting system restoration...")
        logger.info(f"Starting restoration from: {backup_name}")
        
        run_command(cmd, logger, "System restoration", size)
        
        # Report success
        logger.info("Restoration completed successfully")
        print_color("System restoration completed successfully!", "green")
        print(f"Log file: {log_file}")
    
    except Exception as e:
        logger.error(f"Restoration failed: {e}", exc_info=True)
        print_color(f"Error: Restoration failed - {e}", "red")
        sys.exit(1)

def list_restore_points(args):
    """List available restore points"""
    try:
        os.makedirs(RESTORE_BASE_DIR, exist_ok=True, mode=0o700)
        points = []
        
        for entry in RESTORE_BASE_DIR.iterdir():
            if entry.is_dir():
                meta_file = entry / "metadata.json"
                if meta_file.exists():
                    with open(meta_file) as f:
                        metadata = json.load(f)
                        points.append(metadata)
        
        # Sort by timestamp
        points.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Display results
        if not points:
            print("No restore points found")
            return
        
        print(f"{'Name':<25} {'Type':<10} {'Date':<15} {'Size (MB)':>10}")
        print("-" * 65)
        
        for p in points:
            size_mb = p.get("size", 0) / (1024**2)
            date_str = datetime.strptime(p["timestamp"], "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M")
            print(f"{p['name']:<25} {p['type']:<10} {date_str:<15} {size_mb:>10.2f}")
    
    except Exception as e:
        print_color(f"Error: Could not list restore points - {e}", "red")
        sys.exit(1)

def delete_restore_point(args):
    """Delete specified restore point"""
    # Setup logging
    os.makedirs(RESTORE_BASE_DIR, exist_ok=True, mode=0o700)
    os.makedirs(LOGS_DIR, exist_ok=True, mode=0o700)
    logger, log_file = setup_logger("delete")
    
    try:
        backup_name = args.name
        backup_dir = RESTORE_BASE_DIR / backup_name
        
        # Verify existence
        if not backup_dir.exists():
            print_color(f"Error: Restore point '{backup_name}' not found", "red")
            sys.exit(1)
        
        # Confirm deletion
        if not args.force:
            print_color("WARNING: THIS ACTION IS PERMANENT AND IRREVERSIBLE!", "yellow")
            confirmation = input(f"Delete '{backup_name}'? (type 'YES' to confirm): ")
            if confirmation != "YES":
                print("Deletion cancelled")
                sys.exit(0)
        
        # Execute deletion
        logger.info(f"Deleting restore point: {backup_name}")
        shutil.rmtree(backup_dir)
        
        # Report success
        logger.info(f"Deleted successfully: {backup_name}")
        print_color("Restore point deleted successfully!", "green")
        print(f"Log file: {log_file}")
    
    except Exception as e:
        logger.error(f"Deletion failed: {e}", exc_info=True)
        print_color(f"Error: Deletion failed - {e}", "red")
        sys.exit(1)

def main():
    """Main entry point"""
    # Root check
    if os.geteuid() != 0:
        print_color("Error: This tool requires root privileges", "red")
        sys.exit(1)
    
    # Setup argument parser
    parser = argparse.ArgumentParser(
        description="Linux Restore Point - System Snapshot Utility",
        epilog="WARNING: Restore operations are destructive. Use with caution!"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create restore point")
    create_parser.add_argument(
        "--type", 
        choices=["system", "full"], 
        default="system",
        help="Backup type: system (only /etc) or full (with /home)"
    )
    create_parser.add_argument(
        "--include-usb", 
        action="store_true",
        help="Include mounted USB drives in backup"
    )
    
    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore from point")
    restore_parser.add_argument(
        "name", 
        help="Name of restore point to restore"
    )
    restore_parser.add_argument(
        "--force", 
        action="store_true",
        help="Skip confirmation prompt (DANGEROUS)"
    )
    
    # List command
    subparsers.add_parser("list", help="List restore points")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete restore point")
    delete_parser.add_argument(
        "name", 
        help="Name of restore point to delete"
    )
    delete_parser.add_argument(
        "--force", 
        action="store_true",
        help="Skip confirmation prompt"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Check for PV
    if not shutil.which("pv"):
        print_color(
            "Warning: 'pv' command not found. Progress bars disabled.",
            "yellow"
        )
    
    # Execute commands
    try:
        if args.command == "create":
            create_restore_point(args)
        elif args.command == "restore":
            restore_from_point(args)
        elif args.command == "list":
            list_restore_points(args)
        elif args.command == "delete":
            delete_restore_point(args)
    
    except KeyboardInterrupt:
        print_color("\nOperation cancelled by user", "yellow")
        sys.exit(1)
    except Exception as e:
        print_color(f"Unexpected error: {e}", "red")
        sys.exit(1)

if __name__ == "__main__":
    main()
