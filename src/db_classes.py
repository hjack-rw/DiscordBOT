from src.variables import db_connection, db_cursor

from datetime import datetime, timedelta

__all__ = ["ExtraVariables", "Dates"]


class ExtraVariables:
    
    @classmethod
    def set_(cls, db_connection, db_cursor):
        cls.con = db_connection
        cls.cur = db_cursor

    def __init__(self, id):
        self.cur.execute(f"SELECT * FROM extra_variables WHERE ID = {id};")
        self.id, self.type, self.name, var_int = [item for item in self.cur][0]
        self.value = self.get_value(var_int)

    def get_value(self, variable_int):

        if self.type == "bool":
            return bool(variable_int)

    def change_value(self, new_value=None):
        
        # reverse value
        if self.type == "bool":
            self.cur.execute(f"UPDATE extra_variables SET var_int = {int(not self.value)} WHERE ID = {self.id};")
            self.value = not self.value
        
        self.con.commit()


class Dates:

    @classmethod
    def set_(cls, db_connection, db_cursor):
        cls.con = db_connection
        cls.cur = db_cursor
    
    def __init__(self, event):
        self.event, self.all = event, {}

        self.cur.execute(f"SELECT * FROM dates WHERE EVENT = '{event}';")
        for item in self.cur:
            id, _, date_in_int = item
            self.all[convert_to_date(date_in_int)] = id

    # delete date from db
    def delete_date(self, date):
        try:
            id = self.all[date]
            self.cur.execute(f"DELETE FROM dates WHERE ID = {id};")
            del self.all[date]
            
            self.con.commit()
        
        # protect from deleting nonexistant
        except KeyError:
            print("NO SUCH DATE IN DATABASE!")

    # add date to db
    def add_date(self, date):
        date = datetime(year=date.year, month=date.month, day=date.day)
        
        # protect from duplicates
        try:
            self.all[date]
            print("DATE ALREADY IN DATABASE!")
        except KeyError:            
            new_record = (self.event, convert_to_int(date))
            
            self.cur.execute("SELECT * FROM sqlite_sequence WHERE NAME = 'dates';")
            _, id = [item for item in self.cur][0]

            self.cur.execute(f"INSERT INTO dates (event, date_in_int) VALUES {new_record};")
            self.all[date] = int(id) + 1
            
            self.con.commit()
    
    def get_dates(self):
        return list(self.all.keys())


ExtraVariables.set_(db_connection, db_cursor)
Dates.set_(db_connection, db_cursor)


def convert_to_date(date_in_int: int) -> datetime:
    return datetime(year=2000, month=1, day=1) + timedelta(days=date_in_int)

def convert_to_int(date: datetime) -> int:
    origin = datetime(year=2000, month=1, day=1)
    date = datetime(year=date.year, month=date.month, day=date.day)

    delta = origin - date

    return abs(delta.days)