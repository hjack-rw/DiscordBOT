from datetime import datetime, timedelta
from enum import Enum

import copy
import itertools
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


def convert_int_to_date(date_in_int:int):
    try:
        return base_date + timedelta(days=date_in_int)
    except TypeError:
        return None

def convert_date_to_int(date:datetime):
    try:
        date = datetime(year=date.year, month=date.month, day=date.day)
        delta = date - base_date
        return delta.days
    except TypeError:
        return None


def convert_int_to_permutation(permutation_in_int:int, requirements:list):
    permutations = list(itertools.permutations([x for x in range(requirements[0])], requirements[1]))
    return Permutation(max_idx=requirements[0], instance=permutations[permutation_in_int])

def convert_permutation_to_int(permutation:tuple, requirements:list):
    permutations = list(itertools.permutations([x for x in range(requirements[0])], requirements[1]))
    return permutations.index(permutation)


def is_binary(string:str):
    string = set(string)
    if string == {'0', '1'} or string == {'0'} or string == {'1'}:
        return True
    else :
        return False


class Filter(Enum):
    NONE = ""
    ID   = " WHERE ID = 0"
    NAME = " WHERE NAME = '0'"


class Permutation:
    def __init__(self, max_idx, instance):
        self.max_idx      = max_idx
        self.len_instance = len(instance)
        self.instance     = instance
    
    def check(self):
        return (len(set(self.instance)) == self.len_instance) and (max(self.instance) < self.max_idx)


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
        try:
            if type(old_value) != type(new_value):
                raise Exception("Mismatched datatypes!")
            elif type(old_value) == Permutation:
                if type(old_value.instance) != type(new_value.instance) or not new_value.check():
                    raise Exception("Mismatched datatypes!")
        except Exception as exception:
            print(exception)
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

    def _get_value(self, value, type):
        if type == "bool":
            return bool(value)
        elif "binary" in type:
            return ('{0:0' + type.split("_")[1] + 'b}').format(value)
        elif "permutation" in type:
            return convert_int_to_permutation(value, requirements=[int(x) for x in type.split('_') if x != "permutation"])
        elif type == "date":
            return convert_int_to_date(value)
        else:
            return value
    
    def _return_value(self, value, type):
        if type == bool:
            value = int(value)
        elif type == datetime:
            value = convert_date_to_int(value)
        elif type == Permutation:
            value = convert_permutation_to_int(value.instance, requirements=[value.max_idx, value.len_instance])
        elif type == str: 
            if is_binary(value):
                value = int(value, 2)
            else:
                return f"'{value}'"
        return f"{value}"

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
        self.value = self._get_values_from_items(items, self.columns)[0]["value"]

    # change value
    def change(self, to):
        if type(self.value) == Permutation:
            value = copy.deepcopy(self.value)
            value.instance = to
        
            to = value
        
        self.value = self._update(self.table, column="value", id=self.name, old_value=self.value, new_value=to, add=Filter.NAME)
    
    # return value
    def get(self):
        if type(self.value) == Permutation:
            return self.value.instance
        else:
            return self.value


class WelcomeMessages(Database):
    def __init__(self):
        self.table = "welcome_messages"
        self.columns = self._get_columns(self.table)
        self.items = self._select_from(self.table)

    # add message_id to db
    def add(self, message_id):
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
    def add(self, portkey):
        if self.id:
            print("Can only add with full table loaded!")
        else:
            self.items = self._insert(self.table, self.columns, self.items, new_record=portkey)

    # return Portkey / Portkeys
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