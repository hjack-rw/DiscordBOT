from src.variables import db_connection, db_cursor

from datetime import datetime, timedelta
from enum import Enum

__all__ = ["ExtraVariable", "WelcomeMessages", "Portkeys"]


def convert_to_date(date_in_int: int) -> datetime:
    return datetime(year=1900, month=1, day=1) + timedelta(days=date_in_int)

def convert_to_int(date: datetime) -> int:
    origin = datetime(year=1900, month=1, day=1)
    date = datetime(year=date.year, month=date.month, day=date.day)

    delta = origin - date

    return abs(delta.days)


class Filter(Enum):
    NONE = ""
    ID = " WHERE ID = 0"
    NAME = " WHERE NAME = '0'"
    ARCHIVED = " WHERE ARCHIVED = 0"


class Database():
    @classmethod
    def set_(cls, db_connection, db_cursor):
        cls.con = db_connection
        cls.cur = db_cursor

    def _select_from(self, table, id=None, add=Filter.NONE):
        if id and (add != Filter.NONE):
            condition = add.value.replace("0", str(id))
        else:
            condition = add.value
        
        self.cur.execute(f"SELECT * FROM {table}{condition};")
        
        items = {}
        for item in self.cur:
            items[item[1:]] = item[0]
        
        return items
    
    def _get_columns(self, table, drop_columns=[]):
        self.cur.execute(f"PRAGMA table_info({table});")       
        return {item[1]:(item[0] if item[1] not in drop_columns else -1) for item in self.cur if item[1] != "id"}
    
    def _get_value(self, value, type):
        if type == "bool":
            return bool(value)
        elif type == "date":
            return convert_to_date(value)

    def _get_values_from_items(self, items, columns, types=None):
        if types is None:
            types = dict()
        
        instances = items.keys()

        return_list = []
        for instance in instances:
            temp_dict = {}
            
            for idx, column in enumerate(columns.keys()):
                if columns[column] == -1:
                    continue
                elif "type" in column:
                    types.update({column.split("_")[1] : instance[idx]})
                    continue
                
                try:
                    type = types[column]
                    temp_dict[column] = self._get_value(instance[idx], type)
                except KeyError:
                    temp_dict[column] = instance[idx]

            
            return_list.append(temp_dict)
        
        return return_list



class ExtraVariable(Database):
    def __init__(self, name):
        self.name = name
        self.table = "extra_variables"
        self.columns = self._get_columns(self.table, drop_columns=["name"])
        
        items = self._select_from(self.table, id=name, add=Filter.NAME)
        items = self._get_values_from_items(items, self.columns)[0]

        # return value
        self.value = items["value"]

    def change_value(self, new_value=None):
        
        # reverse value
        if self.value == bool:
            self.cur.execute(f"UPDATE {self.table} SET var_int = {int(not self.value)} WHERE NAME = {self.name};")
            self.value = not self.value
        
        self.con.commit()


class WelcomeMessages(Database):
    def __init__(self):
        self.table = "welcome_messages"
        self.columns = self._get_columns(self.table)
        self.items = self._select_from(self.table)

    # add message_id to db
    def add_message_id(self, message_id):
        new_record = (message_id,)
        
        try:
            self.items[new_record]
            print("MESSAGE_ID ALREADY IN DATABASE!")
        except KeyError:            
            _, id = self._select_from(table="sqlite_sequence", id=self.table)

            columns = ", ".join([column for column in self.columns.keys() if self.columns[column] != -1])
            values = ", ".join(str(x) for x in new_record)

            self.cur.execute(f"INSERT INTO {self.table} ({columns}) VALUES ({values});")
            self.items[new_record] = int(id) + 1
            
            self.con.commit()
    
    # return values
    def get_all(self):
        return [instance["message_id"] for instance in self._get_values_from_items(self.items, self.columns)]


class Portkeys(Database):
    def __init__(self, id=None):
        self.id = id
        self.table = "portkeys"
        self.columns = self._get_columns(self.table, drop_columns=["archived"])
        self.types = {"from_wb": "bool", "birthday": "date"}
        
        if self.id:
            self.items = self._select_from(self.table, id, add=Filter.ID)
        else:
            self.items = self._select_from(self.table, add=Filter.ARCHIVED)
    
    # return values
    def get(self):
        # single
        if self.id:
            return self._get_values_from_items(self.items, self.columns, self.types)[0]
        
        # multiple
        else:
            return self._get_values_from_items(self.items, self.columns, self.types)


Database.set_(db_connection, db_cursor)