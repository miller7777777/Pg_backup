# pg_backuper
# Скрипт для резервного копирования баз postgresql с помощью команды pg_dump.
# Version: 1.02
# Authors: Miller777, ChatGPT (https://trychatgpt.ru)
# Date: 2024-10-05

import os
import json
import subprocess
import datetime
import socket
from ftplib import FTP

# Версия скрипта: 1.03
# Дата последнего обновления: 2023-10-05 02:08 (Москва)

def load_settings(settings_file):
    try:
        with open(settings_file, 'r') as f:
            settings = json.load(f)
            # Проверка необходимых параметров
            required_keys = ['pg_dump_path', 'backup_folder', 'max_backups',
                             'host', 'port', 'username', 'ftp_enabled']
            for key in required_keys:
                if key not in settings:
                    raise ValueError(f"Missing required setting: {key}")
            return settings
    except FileNotFoundError:
        log_message("Settings file not found. Please create the settings.json file.", error=True)
        raise
    except json.JSONDecodeError:
        log_message("Error decoding JSON from settings file. Please check the file format.", error=True)
        raise
    except Exception as e:
        log_message(f"Error loading settings: {e}", error=True)
        raise

def load_databases(database_file):
    with open(database_file, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

def log_message(message, error=False):
    with open("pg_backuper.log", "a") as log_file:
        log_file.write(f"{datetime.datetime.now()}: {message}\n\n")
    if error:
        print(f"ERROR: {message}")
    else:
        print(message)

def send_telegram_notification(script_path, status, message):
    command = [script_path, status, message]
    try:
        subprocess.run(command, check=True)
        log_message(f"Telegram notification sent: {message}")
    except subprocess.CalledProcessError as e:
        log_message(f"Error sending telegram notification: {e}", error=True)

def backup_database(pg_dump_path, host, port, username, db_name, backup_folder):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
    backup_file = os.path.join(backup_folder, f"{db_name}_{timestamp}.backup")
    command = [
        pg_dump_path,
        "--file", backup_file,
        "--host", host,
        "--port", port,
        "--username", username,
        "--verbose",
        "--format=c",
        "--blobs",
        db_name
    ]

    try:
        subprocess.run(command, check=True)
        log_message(f"Backup for '{db_name}' created successfully: {backup_file}")
        return backup_file  # Возвращаем имя файла для загрузки на FTP
    except subprocess.CalledProcessError as e:
        log_message(f"Error backing up '{db_name}': {e}", error=True)
        return None

def manage_backups(backup_folder, db_name, max_backups):
    backups = [f for f in os.listdir(backup_folder) if f.startswith(db_name) and f.endswith('.backup')]
    backups.sort()  # Sort by filename (which includes timestamp)

    while len(backups) > max_backups:
        oldest_backup = backups.pop(0)  # Remove the oldest file
        os.remove(os.path.join(backup_folder, oldest_backup))
        log_message(f"Deleted old backup: {oldest_backup}")

def upload_to_ftp(ftp_host, ftp_port, ftp_user, ftp_password, backup_files, target_folder):
    ftp = FTP()
    ftp.connect(ftp_host, ftp_port)
    ftp.login(ftp_user, ftp_password)
    log_message("Connected to FTP server")

    for local_file in backup_files:
        filename = os.path.basename(local_file)
        with open(local_file, 'rb') as f:
            ftp.storbinary(f'STOR {target_folder}/{filename}', f)
            log_message(f"Uploaded {filename} to FTP")

    ftp.quit()
    log_message("Disconnected from FTP server")

def main():
    settings_file = "settings.json"
    database_file = "databases.txt"
    host_name = socket.gethostname()  # Получаем имя компьютера

    try:
        settings = load_settings(settings_file)

    except Exception:
        return

    databases = load_databases(database_file)
    
    backup_files = []

    # Создание резервных копий
    for db in databases:
        backup_file_path = backup_database(settings['pg_dump_path'], settings['host'],
                                           settings['port'], settings['username'], db,
                                           settings['backup_folder'])
        
        if backup_file_path:
            backup_files.append(backup_file_path)
            if settings.get('telegram_notifications_enabled'):
                send_telegram_notification(settings['telegram_script_path'], "r",
                                            f"{settings.get('prefix', '')} {host_name}. Backup for '{db}' created successfully.")
        else:
            if settings.get('telegram_notifications_enabled'):
                send_telegram_notification(settings['telegram_script_path'], "a",
                                            f"{settings.get('prefix', '')} {host_name}. Backup for '{db}' failed.")

        manage_backups(settings['backup_folder'], db, settings['max_backups'])
    
    if settings.get('ftp_enabled') and backup_files:
        upload_to_ftp(settings['ftp_host'], settings['ftp_port'], settings['ftp_user'],
                       settings['ftp_password'], backup_files,
                       settings['ftp_target_folder'])

if __name__ == "__main__":
    main()