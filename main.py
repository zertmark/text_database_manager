import sqlite3
from collections.abc import Callable
from pathlib import Path
from sys import exit

import prettytable


class SQLBase(sqlite3.Connection):
    def __init__(
        self,
        database_path: Path,
        table_name: str = "FILES",
        primary_key_column: str = "file_id",
        fields: list[str] = [],
    ) -> None:
        has_table: bool = database_path.exists()
        self.database_path: Path = database_path
        self.database_table_name: str = table_name
        self.primary_key: str = primary_key_column

        super().__init__(
            database=database_path,
            timeout=5.0,
            detect_types=0,
            isolation_level="DEFERRED",
            check_same_thread=True,
            factory=sqlite3.Connection,
            cached_statements=100,
            uri=False,
        )
        self.cursor_: sqlite3.Cursor = self.new_cursor()
        self.fields: list[str] = fields
        self.MAX_STRING_LINES: int = 100
        if not has_table:
            self.create_table(table_name)

    def row_exists(self, field: str, field_data: str) -> bool:
        return bool(
            self.execute_read_command(
                f"SELECT EXISTS(SELECT 1 FROM {self.database_table_name} WHERE {field}=?);",
                field_data,
            ).fetchone()[0]
        )

    def new_cursor(self) -> sqlite3.Cursor:
        return self.cursor()

    def execute_read_command(self, command: str, *args: str) -> sqlite3.Cursor:
        if sqlite3.complete_statement(command):
            return self.cursor_.execute(command, args)
        raise Exception("Invalid command")

    def create_table(self, table_name) -> None:
        self.execute_write_command(
            """CREATE TABLE IF NOT EXISTS ?(
        file_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
        name TEXT NOT NULL,
        data TEXT NOT NULL);""",
            table_name,
        )
        print("Created TABLE")

    def execute_write_command(self, command: str, *args: str) -> None:
        if sqlite3.complete_statement(command):
            self.cursor_.execute(command, args)
            self.commit()

    # def set_row_info(self, id: int, field: str, new_info: str) -> None:
    #     self.execute_write_command(
    #         "UPDATE ? SET ? = ? WHERE ? = ?;",
    #         self.database_table_name,
    #         field,
    #         new_info,
    #         self.primary_key,
    #         str(id),
    #     )


class Main:
    def __init__(self, database_name: str) -> None:
        self.database = SQLBase(
            database_path=Path.cwd() / "databases" / f"{database_name}.db",
            table_name="FILES",
            fields=["file_id", "name", "data"],
        )
        self.shownTable = prettytable.PrettyTable()
        self.shownTable.field_names = [field.upper() for field in self.database.fields]
        print([field.upper() for field in self.database.fields])
        self.commands: dict[str, Callable[[], None]] = {
            "help": self.get_help,
            "?": self.get_help,
            "add": self.add_file,
            "remove": self.remove_file,
            "show": self.show,
            "write": self.write,
        }

    def get_help(self) -> None:
        print(
            "Current commands are:",
            ", ".join(self.commands.keys()),
            sep="\n---\n",
            end="\n---\n",
        )

    def run(self) -> None:
        while True:
            try:
                command = input("Enter command:").strip()
                if command not in self.commands.keys():
                    continue
                self.commands[command]()
            except KeyboardInterrupt:
                print("\nExiting...")
                self.database.close()
                exit(0)

    def remove_file(self) -> None:
        try:
            file_id = int(input("Enter a file id to remove:"))
            if not self.database.row_exists("file_id", str(file_id)):
                print("Incorrect row")
                return

            self.database.execute_write_command(
                f"DELETE FROM {self.database.database_table_name} WHERE {self.database.primary_key} == ?;",
                str(file_id),
            )
            print(f"Deleted {file_id}")

        except Exception as ex:
            print("Couldn't get the number", str(ex))

    def add_file(self) -> None:
        file = Path(input("Enter a file to add:").strip())
        if not file.exists():
            print("File doesn't exist")
            return

        file_data: str = file.read_text()
        self.database.execute_write_command(
            "INSERT INTO FILES (name, data) VALUES (?, ?);", str(file), file_data
        )
        print(f"Added file {file}")

    def show(self) -> None:
        sql_table = self.database.execute_read_command(
            "SELECT * FROM FILES;"
        ).fetchall()
        self.shownTable.clear_rows()
        for row in sql_table:
            self.shownTable.add_row(list(row))
        print(self.shownTable)

    def write(self) -> None:
        try:
            file_id = int(input("Enter file id:").strip())
            file = Path(input("Enter file path:").strip())
            if not self.database.row_exists("file_id", str(file_id)):
                print("Incorrect id")

            file.write_text(
                self.database.execute_read_command(
                    f"SELECT data FROM FILES WHERE {self.database.primary_key} == ?;",
                    str(file_id),
                ).fetchone()[0],
            )
            print("Written to a file")
        except Exception as ex:
            print(ex)


if __name__ == "__main__":
    Main("test").run()
