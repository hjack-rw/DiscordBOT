from src.variables import db_connection, db_cursor

from datetime import datetime, timedelta

__all__ = ["ExtraVariables"]


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


ExtraVariables.set_(db_connection, db_cursor)


def convert_to_date(date_in_int: int) -> datetime:
    return datetime(year=2000, month=1, day=1) + timedelta(days=date_in_int)

def convert_to_int(date: datetime) -> int:
    origin = datetime(year=2000, month=1, day=1)
    date = datetime(year=date.year, month=date.month, day=date.day)

    delta = origin - date

    return abs(delta.days)