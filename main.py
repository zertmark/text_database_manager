import sqlite3, os
import prettytable

class fileHandler:    

    @staticmethod
    def read_bytes_from_file(file_path):
        out = ""
        with open(file_path, "r", encoding="UTF-8") as file:
            return "".join(file.readlines())

    @staticmethod
    def write_bytes_to_file(file_path, output):
            with open(file_path, "w", encoding="UTF-8") as file:
                file.write(output)

class SQLBase(sqlite3.Connection):

    def __init__(self, database_path:str = "", table_name:str = 'FILES', primary_key_column:str = "file_id", fields:list = []) -> None:            
        has_table = self.checkDatabasesPath(database_path)
        self.databasePath:str = database_path
        self.dataBaseTableName:str = table_name 
        self.primaryKey:str = primary_key_column           

        super().__init__(database_path,5.0,0,"DEFERRED",True,sqlite3.Connection, 100, False)
        self.Cursor:sqlite3.Cursor = self.newCursor()
        self.__rowsCount:int = 0    
        self.fields:list = fields
        self.MAX_STRING_LINES:int = 100
        if not has_table:
            self.createTable(table_name)
            
    def rowExists(self, field:str, field_data) -> bool:
        return True if self.executeReadCommand(f"SELECT EXISTS(SELECT 1 FROM {self.dataBaseTableName} WHERE {field}=?);", (field_data,)).fetchone()[0] else False 

    def checkDatabasesPath(self, path:str = "") -> bool:
        return os.path.exists(path)
        
    def newCursor(self) -> sqlite3.Cursor:
        return self.cursor()

    def executeReadCommand(self, command, *args) -> object:
        if sqlite3.complete_statement(command):
            return self.Cursor.execute(command, *args)

    def createTable(self, table_name):
        self.executeWriteCommand(
        f"""CREATE TABLE IF NOT EXISTS {table_name}(
        file_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
        name TEXT NOT NULL,
        data TEXT NOT NULL);""")
        print("Created TABLE")
        
        
    def executeWriteCommand(self, command, *args) -> None:
        if sqlite3.complete_statement(command):
            self.Cursor.execute(command ,*args)
            self.commit()
    
    def setRowInfo(self, id:int, field:str, new_info) -> None:
        self.executeWriteCommand(f"UPDATE {self.dataBaseTableName} SET {field} = ? WHERE {self.primaryKey} = ?;", (new_info,id))


class Main:
    def __init__(self, database_name):
        self.database = SQLBase(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), f"databases/{database_name}.db"),
            table_name = "FILES",
            fields = ["file_id", "name", "data"])
        self.shownTable = prettytable.PrettyTable()
        self.shownTable.field_names = [field.upper() for field in self.database.fields]
        print([field.upper() for field in self.database.fields])
        self.commands = {
            "?": self.getHelp,
            "add": self.addFile,
            "remove": self.removeFile,
            "show": self.show,
            "write": self.write
        }
        
    
    def getHelp(self):
        print("Current commands are:", ', '.join(self.commands.keys()), sep="\n---\n", end="\n---\n")
        
    def Run(self):
        running = True
        while running:
            try:
                command = input("Enter command:").strip()
                if command not in self.commands.keys():
                    continue
                                    
                self.commands[command]()

            except KeyboardInterrupt: 
                print("\nExiting...")
                self.database.close()
                exit(0)

    def removeFile(self):
        try:
            file_id = int(input("Enter a file id to remove:"))
            if not self.database.rowExists("file_id", file_id):
                print("Incorrect row")
                return
                
            # print(self.database.primary_key)
            self.database.executeWriteCommand(f"DELETE FROM {self.database.dataBaseTableName} WHERE {self.database.primaryKey} == {file_id};")
            print(f"Deleted {file_id}")

        except Exception as ex:
             print("Couldn't get the number", str(ex))
        
    def addFile(self):
        file_path = input("Enter a file to add:").strip()
        if not os.path.exists(file_path):
            print("File doesn't exist")
            return
            
        file_data:str = fileHandler.read_bytes_from_file(file_path) 
        self.database.executeWriteCommand("INSERT INTO FILES (name, data) VALUES (?, ?);", (file_path, file_data))
        print(f"Added file {file_path}")

    def show(self):
        sql_table = self.database.executeReadCommand("SELECT * FROM FILES;").fetchall()
        self.shownTable.clear_rows()
        for row in sql_table:
            self.shownTable.add_row(list(row))
        print(self.shownTable)            

    def write(self):
        try:
            file_id = int(input("Enter file id:").strip())
            file_path = input("Enter file path:").strip()
            if not self.database.rowExists("file_id", file_id):
                print("Incorrect id")
                
            fileHandler.write_bytes_to_file(file_path, self.database.executeReadCommand(f"SELECT data FROM FILES WHERE {self.database.primaryKey} == {file_id};").fetchone())
            print("Written to a file")
        except Exception:
            pass
                        
if __name__ == "__main__":
    main = Main("test")
    main.Run()