### Описание работы скрипта резервного копирования для начинающих программистов

Этот скрипт предназначен для автоматизации процесса резервного копирования баз данных PostgreSQL. Он написан на Python и использует стандартные библиотеки, а также библиотеки для работы с PostgreSQL. Давайте подробно рассмотрим каждую его часть и основные концепции, которые могут быть полезны при изучении Python.

#### Основные компоненты скрипта

1. **Импорт библиотек**:
   python
   import os
   import json
   import subprocess
   import datetime
   import socket
   from ftplib import FTP
   
   Здесь мы импортируем необходимые библиотеки:
   - `os`: Для работы с операционной системой (например, для работы с файлами).
   - `json`: Для обработки JSON-файлов, текстового формата, используемого для хранения настроек.
   - `subprocess`: Для выполнения команд в командной строке (например, команды резервного копирования).
   - `datetime`: Для работы с датой и временем.
   - `socket`: Для получения информации о хосте.
   - `ftplib`: Для загрузки файлов на FTP-сервер.

2. **Загрузка настроек**:
   python
   def load_settings(settings_file):
       with open(settings_file, 'r') as f:
           return json.load(f)
   
   Функция `load_settings` открывает файл настроек `settings.json` и загружает его содержимое как словарь Python. Мы используем метод `json.load()` для этой задачи.

3. **Загрузка списка баз данных**:
   python
   def load_databases(database_file):
       with open(database_file, 'r') as f:
           return [line.strip() for line in f if line.strip()]
   
   В этой функции мы открываем файл `databases.txt`, считываем название баз данных и очищаем строки от лишних пробелов. Мы используем списковое включение для создания списка баз данных.

4. **Функции для резервного копирования**:
   python
   def backup_database(pg_dump_path, host, port, username, db_name, backup_folder):
       timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
       backup_file = os.path.join(backup_folder, f"{db_name}_{timestamp}.backup")

       command = [pg_dump_path, "-h", host, "-p", str(port), "-U", username, "-F", "c", "--file", backup_file, db_name]
       subprocess.run(command, check=True)
       return backup_file
   
   Эта функция создает резервные копии баз данных с помощью утилиты `pg_dump`. Мы формируем команду, которая включает путь к утилите и параметры подключения. Метод `subprocess.run()` позволяет выполнить команду в командной строке.

5. **Управление резервными копиями**:
   python
   def manage_backups(backup_folder, db_name, max_backups):
       backups = [f for f in os.listdir(backup_folder) if f.startswith(db_name) and f.endswith('.backup')]
       backups.sort()

       while len(backups) > max_backups:
           oldest_backup = backups.pop(0)
           os.remove(os.path.join(backup_folder, oldest_backup))
   
   Эта функция управляет резервными копиями, удаляя старые, если их количество превышает указанное значение `max_backups`.

6. **Загрузка на FTP**:
   python
   def upload_to_ftp(ftp_host, ftp_port, ftp_user, ftp_password, backup_files, target_folder):
       ftp = FTP()
       ftp.connect(ftp_host, ftp_port)
       ftp.login(ftp_user, ftp_password)

       for local_file in backup_files:
           with open(local_file, 'rb') as f:
               ftp.storbinary(f'STOR {target_folder}/{os.path.basename(local_file)}', f)
       ftp.quit()
   
   Эта функция загружает резервные копии на FTP-сервер. Мы подключаемся к серверу, а затем загружаем каждый файл по очереди.

7. **Основная функция**:
   python
   def main():
       settings_file = "settings.json"
       database_file = "databases.txt"
       host_name = socket.gethostname()

       settings = load_settings(settings_file)
       databases = load_databases(database_file)

       backup_files = []

       for db in databases:
           if not db.startswith("#"):  # Проверка на исключенные базы
               backup_file_path = backup_database(settings['pg_dump_path'], settings['host'],
                                                  settings['port'], settings['username'], db,
                                                  settings['backup_folder'])
               backup_files.append(backup_file_path)

       manage_backups(settings['backup_folder'], db, settings['max_backups'])

       if settings.get('ftp_enabled') and backup_files:
           upload_to_ftp(settings['ftp_host'], settings['ftp_port'],
                          settings['ftp_user'], settings['ftp_password'],
                          backup_files, settings['ftp_target_folder'])
   
   В этой функции осуществляется основная логика работы скрипта: загрузка настроек, создание резервных копий баз данных, управление ими и загрузка на FTP.

8. **Запуск скрипта**:
   python
   if __name__ == "__main__":
       main()
   
   Эта конструкция позволяет запустить функцию `main()` только если файл запущен как основной модуль.

### Объяснение основных концепций Python

- **Функции**: В Python функции определяются с помощью ключевого слова `def`. Они позволяют организовывать код и избежать дублирования.
- **Словари**: Словари — это структуры данных, которые хранят пары ключ-значение. В этом скрипте мы используем словари для хранения настроек и параметров.
- **Работа с файлами**: Oткрытие и чтение файлов осуществляется с помощью контекстного менеджера (`with open(...) as ...:`), что гарантирует, что файлы будут закрыты после использования.
- **Модули**: Использование библиотек и модулей (например, `os`, `json`) позволяет расширять функциональность вашего кода и упрощает решение различных задач.
- **Обработка ошибок**: Скрипт предполагает наличие ошибок (например, если база данных не существует), что делает его более устойчивым. В реальном проекте стоит добавить дополнительные блоки обработки ошибок.

### Заключение

Этот скрипт является хорошим примером применения Python для решения реальной задачи - резервного копирования данных. Изучая его, вы познакомитесь с базовыми концепциями программирования на Python и научитесь работать с файлами, командной строкой и внешними библиотеками. Учитесь на примерах, экспериментируйте и модифицируйте код, чтобы лучше понять, как он работает!