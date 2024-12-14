from src.variables import db_connection, db_cursor

from datetime import datetime, timedelta

__all__ = ["ExtraVariables"]


class Database():
    @classmethod
    def set_(cls, db_connection, db_cursor):
        cls.con = db_connection
        cls.cur = db_cursor

    def select_from(self, table, id=None):
        add = (f" WHERE NAME = '{id}'" if table == "sqlite_sequence" else f" WHERE ID = {id}") if id else ""
        self.cur.execute(f"SELECT * FROM {table}{add};")
        
        all, item = {}, ()
        for item in self.cur:
            all[item[1:]] = item[0]
        
        if id:
            return item
        else:
            return all
    
    def get_columns(self, table, drop_id=True):
        self.cur.execute(f"PRAGMA table_info({table});")
        
        if drop_id:
            return [item[1] for item in self.cur if item[1] != "id"]
        else:
            return [item[1] for item in self.cur]


class ExtraVariables(Database):
    def __init__(self, id):
        self.table = "extra_variables"
        
        self.id, self.type, self.name, var_int = self.select_from(self.table, id)
        self.value = self.get_value(var_int)

    def get_value(self, variable_int):

        if self.type == "bool":
            return bool(variable_int)

    def change_value(self, new_value=None):
        
        # reverse value
        if self.type == "bool":
            self.cur.execute(f"UPDATE {self.table} SET var_int = {int(not self.value)} WHERE ID = {self.id};")
            self.value = not self.value
        
        self.con.commit()


class WelcomeMessages(Database):
    def __init__(self):
        self.table = "welcome_messages"
        self.all = self.select_from(self.table)

    # add message_id to db
    def add_message_id(self, message_id):
        new_record = (message_id,)
        
        try:
            self.all[new_record]
            print("MESSAGE_ID ALREADY IN DATABASE!")
        except KeyError:            
            _, id = self.select_from(table="sqlite_sequence", id=self.table)

            columns = ", ".join(self.get_columns(self.table))
            values = ", ".join(str(x) for x in new_record)

            self.cur.execute(f"INSERT INTO {self.table} ({columns}) VALUES ({values});")
            self.all[new_record] = int(id) + 1
            
            self.con.commit()
    
    def get_message_ids(self):
        return [record[0] for record in self.all.keys()]


Database.set_(db_connection, db_cursor)


def convert_to_date(date_in_int: int) -> datetime:
    return datetime(year=1900, month=1, day=1) + timedelta(days=date_in_int)

def convert_to_int(date: datetime) -> int:
    origin = datetime(year=1900, month=1, day=1)
    date = datetime(year=date.year, month=date.month, day=date.day)

    delta = origin - date

    return abs(delta.days)