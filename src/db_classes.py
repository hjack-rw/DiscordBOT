from datetime import datetime, timedelta
from enum import Enum

import os
import sqlite3

def connect_db():
    try:
        path = os.getcwd() + "/src/"
        db = sqlite3.connect(path + '_database.db')
    except sqlite3.Error as error:
        print(error)
    finally:
        return db, db.cursor()
    
db_connection, db_cursor = connect_db()
base_date = datetime(year=2000, month=1, day=1)

__all__ = ["ExtraVariable", "WelcomeMessages", "Portkeys"]


def convert_to_date(date_in_int: int):
    try:
        return base_date + timedelta(days=date_in_int)
    except TypeError:
        return None

def convert_to_int(date: datetime):
    try:
        date = datetime(year=date.year, month=date.month, day=date.day)
        delta = date - base_date
        return delta.days
    except TypeError:
        return None

def is_binary(string: str):
    string = set(string)
    if string == {'0', '1'} or string == {'0'} or string == {'1'}:
        return True
    else :
        return False


class Filter(Enum):
    NONE = ""
    ID   = " WHERE ID = 0"
    NAME = " WHERE NAME = '0'"


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

        return {item[1:]:item[0] for item in self.cur}
    
    def _update(self, table, column, id, old_value, new_value, add=Filter.ID):
        if type(old_value) != type(new_value):
            print("Mismatched datatypes!")
            return old_value

        condition = add.value.replace("0", str(id))
        change = self._return_value(new_value, type(new_value))

        command = f"UPDATE {table} SET {column} = {change}{condition};".replace("None", "NULL")
        self.cur.execute(command)
        self.con.commit()
        return new_value

    def _insert(self, table, columns, items, new_record):
        # protect from creating duplicates
        try:
            items[new_record]
            print(f"{new_record} is already in the database!")
        except KeyError:
            id = list(self._select_from(table="sqlite_sequence", id=table, add=Filter.NAME).keys())[0]

            columns = ", ".join([column for column in columns.keys() if columns[column] != -1])
            values = ", ".join([self._return_value(record, type(record)) for record in new_record])

            try:
                command = f"INSERT INTO {table} ({columns}) VALUES ({values});".replace("None", "NULL")
                self.cur.execute(command)
                self.con.commit()
            except sqlite3.IntegrityError:
                raise ValueError("failed to add to the database")
            
            items[new_record] = int(id[0]) + 1
        
        return items

    def _delete(self, table, items, record):
        # protect from deleting nonexistant
        try:
            id = items[record]
            self.cur.execute(f"DELETE FROM {table} WHERE ID = {id};")
            self.con.commit()
            del items[record]
        except KeyError:
            print(f"No {record} record in the database!")
        
        return items

    def _get_columns(self, table, drop_columns=[]):
        self.cur.execute(f"PRAGMA table_info({table});")       
        #(item[0] if item[1] not in drop_columns else -1)
        return {item[1]:item[0] for idx,item in enumerate(self.cur) if idx != 0}
    
    def _return_value(self, value, type):
        if type == bool:
            value = int(value)
        elif type == datetime:
            value = convert_to_int(value)
        elif type == str: 
            if is_binary(value):
                value = int(value, 2)
            else:
                return f"'{value}'"
        return f"{value}"

    def _get_value(self, value, type):
        if type == "bool":
            return bool(value)
        elif type == "date":
            return convert_to_date(value)
        elif "binary" in type:
            string = '{0:0'+ type.split("_")[1] + 'b}'
            return string.format(value)
        else:
            return value

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

            
            return_list += [temp_dict]
        
        return return_list



class ExtraVariable(Database):
    def __init__(self, name):
        self.table = "extra_variables"
        self.columns = self._get_columns(self.table)
        self.name = name
        
        items = self._select_from(self.table, id=name, add=Filter.NAME)
        items = self._get_values_from_items(items, self.columns)[0]

        # return value
        self.value = items["value"]

    # change value
    def change_value(self, to):
        self.value = self._update(self.table, column="value", id=self.name, old_value=self.value, new_value=to, add=Filter.NAME)


class WelcomeMessages(Database):
    def __init__(self):
        self.table = "welcome_messages"
        self.columns = self._get_columns(self.table)
        self.items = self._select_from(self.table)

    # add message_id to db
    def add_message_id(self, message_id):
        new_record = (message_id,)
        self.items = self._insert(self.table, self.columns, self.items, new_record)
    
    # return message_ids
    def get_all(self):
        return [instance["message_id"] for instance in self._get_values_from_items(self.items, self.columns)]


class Portkeys(Database):
    def __init__(self, id=None):
        self.table = "portkeys"
        self.columns = self._get_columns(self.table)
        self.types = {"from_wb": "bool", "multiple_choice": "binary_13", "birthday": "date", "archived": "bool"}
        
        if id is None:
            self.id = None
            self.items = self._select_from(self.table)
        else:
            self.id = self.last_portkey() if (id == "last") else id
            self.items = self._select_from(self.table, self.id, add=Filter.ID)
    
    # get last Portkey id
    def last_portkey(self):
        return list(self._select_from(table="sqlite_sequence", id=self.table, add=Filter.NAME).keys())[0][0]

    # add Portkey
    def add_portkey(self, portkey):
        if self.id:
            print("Can only add with full table loaded!")
        else:
            self.items = self._insert(self.table, self.columns, self.items, new_record=portkey)

    # return Portkeys
    def get(self):
        if self.id:
            # single record
            dict = {"id": self.id}
            dict.update(self._get_values_from_items(self.items, self.columns, self.types)[0])
            return dict
        else:
            # multiple (for birthdays)
            items = self._get_values_from_items(self.items, self.columns, self.types)
            return [{key:value for key,value in item.items() if key in ["user_id", "birthday"]} for item in items if item["archived"] == False]


Database.set_(db_connection, db_cursor)