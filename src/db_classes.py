from datetime import datetime, timedelta
from enum import Enum

import copy
import itertools
import os
import sqlite3


# Data conversions operations
############################################################################################################

# date
base_date = datetime(year=2000, month=1, day=1)

def convert_int_to_date(date_in_int:int):
    return base_date + timedelta(days=date_in_int)

def convert_date_to_int(date:datetime):
    date = datetime(year=date.year, month=date.month, day=date.day)
    delta = date - base_date
    return delta.days

# binary
def is_binary(string:str):
    string = set(string)
    if string == {'0', '1'} or string == {'0'} or string == {'1'}:
        return True
    return False

# permutation
class permutation:
    def __init__(self, permutation_in_int:int, requirements:list):
        self.max_idx, self.len_instance = [int(x) for x in requirements[1:]]

   #def convert_int_to_permutation
        self.instance = self.permutations()[permutation_in_int]
    
    def permutations(self):
        return list(itertools.permutations([x for x in range(self.max_idx)], self.len_instance))

    def check(self):
        test_1 = (type(self.instance) == tuple)
        test_2 = (len(self.instance)  == self.len_instance)
        test_3 = (max(self.instance)   < self.max_idx)
        return test_1 and test_2 and test_3

    def convert_permutation_to_int(self):
        return self.permutations().index(self.instance)

# Validators
############################################################################################################

# check the variable in question (== True)
def check_variable(self, variables:list, reverse=False):
    """Check the variables in question if == True"""

    check = False

    for name in variables:
        try:
            if check := vars(self)[name]:
                break
        except KeyError:
            continue
    
    return not check if reverse else check

def sql_insert_delete_operation_validator(func):
    """Validator if the table was loaded fully"""

    def validator(self, *args, **kwargs):
        if not check_variable(self, variables=["conditions", "is_short"]):
            return func(self, *args, **kwargs)
        
        # print error not to interrupt app
        print(f"Can only '{func.__name__}' with fully loaded table!")
    
    return validator

def sql_update_one_operation_validator(func):
    """Validate if more than one record was loaded"""

    def validator(self, *args, **kwargs):
        if len(self.raw) < 2 and not check_variable(self, variables=["is_short"]):
            return func(self, *args, **kwargs)
        
        # print error not to interrupt app
        print(f"Can only '{func.__name__}' with one record loaded!")
    
    return validator

def sql_entire_table_init_validator(func):
    """Validator for tables that need all rows loaded"""

    def validator(self, *args, **kwargs):
        for kwarg in kwargs:
            if kwarg in ["omitted_columns", "specified_columns"]:
                raise Exception(f"Needs to load all rows for '{self.__name__}'!")
        return func(self, *args, **kwargs)
    
    return validator

# Clauses
############################################################################################################

class Filter(Enum):
    NONE     = ""
    STANDARD = " = *"
    BOOL_T   = "* = 1"
    BOOL_F   = "* = 0"
    NULL     = "* IS NULL" 

def check_type(key, value, type, req_numeric=False):
    if type == "undefined":
        if not isinstance(value, int) or not isinstance(value, float):
            raise Exception(f"'{key}' is neither an int nor a float!")
    
    elif type == "permutation":
        if not value.check():
            raise Exception(f"'{key}' is not a suited permutation!")
    
    elif type == "binary":
        if not isinstance(value, str) and not is_binary(value):
            raise Exception(f"'{key}' is not binary!")
    
    else:
        type_dict = {"int":int,"float":float,"str":str,"datetime":datetime}
        
        if not isinstance(value, type_dict[type]):
            raise Exception(f"'{key}' is not a {type}!")
    
    if req_numeric:
        raise Exception(f"'{key}' has not a numeric filter!")
    
    return True

def get_clause(conditions):
    """Get the condition clause"""

    if conditions and (Filter.NONE not in conditions):
        clause = " AND ".join([f"{con}" for con in conditions])

        if "*" not in clause:
            return  "WHERE " + clause
        
        print(f"An error occurred while applying the filter:\n'{clause}'")
    return Filter.NONE.value

def get_update_clause(self, new_value):
    """Get update clause"""
    
    # get the record
    id, record = zip(*self.raw.items())
    id, record = next(iter(id)), next(iter(record))

    record = list(record)
    
    update_clause = []
    for column,value in new_value.items():
        
        # get column_id
        try:
            column_id = list(self.columns.keys())[1:].index(column)
        except ValueError:
            if column == self._get_id_column():
                raise Exception(f"{column} is an ID!")
            raise Exception(f"{column} is not a column name!")

        # get the old value string
        _, value_type, not_null, _  = self.columns[column].values()
                
        # get the old value
        old_value = self._get_value(record[column_id], self._get_type_from_column(value_type))

        # protect from mismatched datatypes (except None)
        if not_null:
            try:
                if type(old_value) != type(value):
                    raise Exception("Mismatched datatypes!")
                elif type(old_value) == permutation:
                    if not value.check():
                        raise Exception("Mismatched datatypes!")
            except Exception as exception:
                print("Error: ", exception)
                value = old_value

        # convert to db value
        change = self._return_value(value, type(value))
    
        update_clause += [f"{column} = {change}"]

        record[column_id] = change
    return ", ".join(update_clause), id, record


# Basic SQL commands and functionality
############################################################################################################

class Database():
    @classmethod
    def set_(cls, db_connection, db_cursor):
        cls.con = db_connection
        cls.cur = db_cursor

    def _select(self, table, conditions=[Filter.NONE], is_short=False):
        """Command SELECT"""

        # apply filters
        clause = get_clause(conditions)

        # apply selected columns
        columns = "*"
        if is_short:
            columns = ", ".join(self._get_imported_columns()).upper()

        # execute command
        try:
            command = f"SELECT {columns} FROM {table} {clause};"
            self.cur.execute(command)
        except sqlite3.OperationalError:
            print("Error:", command)
        
        return {row[0]:tuple(row[1:]) for row in self.cur}

    def _update(self, conditions, new_value):
        """Command UPDATE"""
        
        # apply filters
        clause = get_clause(conditions)
        
        update_clause, id, record = get_update_clause(self, new_value)

        # execute command
        try:
            command = f"UPDATE {self.table} SET {update_clause} {clause};".replace("None", "NULL")
            self.cur.execute(command)
            self.con.commit()
        except sqlite3.OperationalError:
            print("Error:", command)
        
        # replace the changed value in record
        self.raw[id] = tuple(record)

    def _insert(self, new_record, custom_id=None):
        """Command INSERT"""
        
        # protect from creating duplicates
        try:
            {value:key for key,value in self.raw.items()}[new_record]
            print(f"{new_record} is already in the database!")

        # if not a duplicate
        except KeyError:
            
            new_record = [self._return_value(value, type(value)) for value in new_record]

            # when using a custom_id column
            if custom_id is not None:
                custom_id = self._return_value(custom_id, type(custom_id))
                
                columns     = filter(lambda item: not item[1]["has_default"], self.columns.items())
                id, values  = custom_id, (custom_id, *new_record)
            
            # else autoiterate
            else:
                columns     = filter(lambda item: not item[1]["has_default"] and not item[1]["is_pk"], self.columns.items())
                id, values  = self._get_last_id() + 1, new_record

            columns = ", ".join([column for column,_ in columns]).upper()
            values  = ", ".join([str(value) for value in values])

            # execute command
            try:
                command = f"INSERT INTO {self.table} ({columns}) VALUES ({values});".replace("None", "NULL")
                self.cur.execute(command)
                self.con.commit()
            except sqlite3.IntegrityError:
                raise Exception(f"failed to add to the database! Error: {command}")
            
            # insert the new record
            self.raw[id] = tuple(new_record)

    def _delete(self, conditions, id):
        """Command DELETE"""
        
        # apply filters
        clause = get_clause(conditions)
        
        # protect from deleting nonexistant
        try:
            record = self.raw[id]
            
            # execute command
            command = f"DELETE FROM {self.table} {clause};"
            self.cur.execute(command)
            self.con.commit()
            del self.raw[id]
        
            # return the deleted record
            return {id: record}

        # if doesn't exitst
        except KeyError:
            print(f"no such record in the database! Error: {command}")
            return None

    def _get_columns(self, types={}, **kwargs):
        """Get column names"""
        
        types_dict = {"INTEGER":"int",
                      "REAL":"float", 
                      "NUMERIC":"undefined", # Float or Int
                      "TEXT":"str",
                      "BLOB": "object"}      # Binary Large Object
        
        types_dict.update(types)

        omitted_columns   = kwargs.pop("omitted_columns",   [])
        specified_columns = kwargs.pop("specified_columns", [])

        # protect from excluding specified
        if omitted_columns in specified_columns:
            raise Exception(f"'specified_columns' and 'omitted_columns' can't overlap")
        
        # execute command
        self.cur.execute(f"PRAGMA table_info({self.table});")       

        columns = {}
        for (_, column_name, type, not_null, has_default, is_pk) in self.cur:

            # keep pk
            if not is_pk:
                if (specified_columns and column_name not in specified_columns) or (column_name in omitted_columns):
                    columns[column_name] = None
                    continue
            
            columns[column_name] = {"is_pk":       bool(is_pk),
                                    "type":        types_dict.pop(column_name, types_dict[type]),
                                    "not_null":    bool(not_null),
                                    "has_default": bool(has_default)}

        # columns dict {"column_name":True/False}
        return columns, kwargs

    def _get_filters(self, **kwargs):
        """ Return filters for DB """
        
        allowed_filters = list(self._get_imported_columns())

        self.conditions, self.is_short = [], not all((self.columns.values()))
        for key, value in kwargs.items():
            
            # specification for certain variables
            try:
                key, spec = key.split("__")
            except ValueError:
                key, spec = next(iter(key.split("__"))), None
            
            if key not in allowed_filters:
                raise Exception(f"filter '{key}' can't be applied to the requested data/table!")
            
            type = self.columns[key]["type"]
            spec_is_numeric = True if spec and spec != "inequal" else False

            # if value has the correct type apply conditions
            if type != "bool":
                
                # int, float, undefined, datetime, binary
                if type not in ["str", "permutation"]:
                    if type == "int":

                        # except accepted keywords
                        if key == "id" and value in ["last"]:
                            value = self._get_last_id()
                        
                        elif key == "message_id" and value in ["archived", "unarchived"]:
                            self.conditions += [Filter.NULL.value.replace("*", key.upper())]
                        
                            if value == "unarchived":
                                self.conditions[-1] = self.conditions[-1].replace("IS", "IS NOT")
                            
                            continue
                        
                        elif isinstance(value, str):
                            raise Exception(f"'{value}' is not an accepted keyword!")

                    check_type(key, value, type)
                
                # string, permutation
                else:
                    if "permutation" in type:
                        permutation = permutation(0, requirements=type.split('_'))
                        permutation.instance = value
                        value = permutation
                
                    check_type(key, value, type, req_numeric=spec_is_numeric)

                self.conditions += [key.upper() + Filter.STANDARD.value.replace("*", str(self._return_value(value, type)))]

            # bool
            elif type == "bool" and check_type(key, value, type, req_numeric=spec_is_numeric):
                filter = Filter.BOOL_T if value else Filter.BOOL_F
                self.conditions += [filter.value.replace("*", key.upper())]
            
            # apply specification
            if spec:
                if spec == "less":
                    self.conditions[-1] = self.conditions[-1].replace("=", "<")
                elif spec == "lessequal":
                    self.conditions[-1] = self.conditions[-1].replace("=", "<=")
                elif spec == "great":
                    self.conditions[-1] = self.conditions[-1].replace("=", ">")
                elif spec == "greatequal":
                    self.conditions[-1] = self.conditions[-1].replace("=", ">=")
                elif spec == "inequal":
                    self.conditions[-1] = self.conditions[-1].replace("=", "<>")

        return self.conditions, self.is_short

    def _get_value(self, value, type):
        """ Convert out of DB value """

        if type == "bool":
            return bool(value)
        elif "binary" in type:
            return ('{0:0' + type.split("_")[1] + 'b}').format(value)
        elif "permutation" in type:
            return permutation(value, requirements=type.split('_'))
        elif type == "datetime":
            return convert_int_to_date(value)
        return value
    
    def _return_value(self, value, type):
        """ Convert to DB value """

        try:
            type = type.__name__
        except AttributeError:
            pass

        if type == "bool":
            value = int(value)
        elif type == "datetime":
            value = convert_date_to_int(value)
        elif type == "permutation":
            value = value.convert_permutation_to_int()
        elif type in ["str", "binary"]: 
            if is_binary(value):
                value = int(value, 2)
            else:
                return f"'{value}'"
        return value

    def _get_values_from_raw_data(self, raw, add_id=False):
        """ Return records in a list of dict """
        
        return_list = []
        for idx, instance in raw.items():
            temp_dict = {}
            
            for idx_column, column in enumerate(self._get_imported_columns(), -1):
                is_pk , value_type, _, _  = self.columns[column].values()
                
                if is_pk:
                    if add_id:
                        temp_dict[column] = idx
                    continue
                
                temp_dict[column] = self._get_value(instance[idx_column], self._get_type_from_column(value_type))
            
            return_list += [temp_dict]
        
        return return_list

    def _get_type_from_column(self, type):
        if isinstance(type, int):
            return next(iter(self.raw.values()))[type]
        return type

    # TODO! Only one ID supported at the time, the first Primary Key
    def _get_id_column(self):
        return next(filter(lambda item: item[1]["is_pk"], self.columns.items()))[0]

    def _get_imported_columns(self):
        return filter(self.columns.get, self.columns)

    def _get_last_id(self):
        return int(next(iter(self._select(table="sqlite_sequence", conditions=["NAME" + Filter.STANDARD.value.replace("*", f"'{self.table}'")]).values()))[0])

# Tables
############################################################################################################

class ExtraVariable(Database):
    
    @sql_entire_table_init_validator
    def __init__(self, **kwargs):
        self.table           = "extra_variables"
        self.columns, kwargs = self._get_columns(types={"value":0}, **kwargs)
        self.raw             = self._only_one_variable(self._select(self.table, *self._get_filters(**kwargs)))
    
    # on at the time ExtraVariable validator
    def _only_one_variable(self, raw):
        if len(raw) > 1:
            raise Exception(f"{self.table} can only be loaded one at the time!")
        return raw

    # change the value of ExtraVariable
    def change(self, to):
        value = next(iter(self._get_values_from_raw_data(self.raw)))["value"]
        
        if type(value) == permutation:
            value = copy.deepcopy(value)
            value.instance = to
            to = value
        
        self._update(conditions=self.conditions, new_value={"value":to})

    # return ExtraVariable
    def get(self):
        value = next(iter(self._get_values_from_raw_data(self.raw)))["value"]
        if type(value) == permutation:
            return value.instance
        return value


class WelcomeMessages(Database):
    def __init__(self, **kwargs):
        self.table           = "welcome_messages"
        self.columns, kwargs = self._get_columns(types={"date":"datetime"}, **kwargs)
        self.raw             = self._select(self.table, *self._get_filters(**kwargs))

    # add WelcomeMessage
    @sql_insert_delete_operation_validator
    def add(self, user_id, message_id, date):
        self._insert(new_record=(message_id, date), custom_id=user_id)
    
    # remove WelcomeMessage
    @sql_insert_delete_operation_validator
    def remove(self, user_id):
        if deleted_record := self._delete(conditions=[self._get_id_column().upper() + Filter.STANDARD.value.replace("*", str(user_id))], id=user_id):
            return next(iter(self._get_values_from_raw_data(deleted_record)))["message_id"]
        return None

    # return WelcomeMessages
    def get_all(self):
        return self._get_values_from_raw_data(self.raw, add_id=True)


class Portkeys(Database):
    def __init__(self, **kwargs):
        self.table           = "portkeys"
        self.columns, kwargs = self._get_columns(types={"from_wb":"bool", "multiple_choice":"binary_13", "birthday":"datetime"}, **kwargs)
        self.raw             = self._select(self.table, *self._get_filters(**kwargs))
    
    # add Portkey
    @sql_insert_delete_operation_validator
    def add(self, portkey):
        self._insert(new_record=portkey)
    
    # update Portkey
    @sql_update_one_operation_validator
    def unarchive(self, message_id):
        self._update(conditions=self.conditions, new_value={"message_id":message_id})

    # archive Portkey
    @sql_update_one_operation_validator
    def archive(self):
        try:
            message_id = self.get()["message_id"]
            self._update(conditions=self.conditions, new_value={"message_id":None})
            return message_id
        except TypeError:
            return None

    # return Portkey / Portkeys
    def get(self, multiple=False):
        if not multiple:
            try:
                return self._get_values_from_raw_data(self.raw)[0]
            except IndexError:
                return None
        return [portkey["user_id"] for portkey in self._get_values_from_raw_data(self.raw)]

############################################################################################################

def connect_db():
    """Access database"""
    try:
        path = os.getcwd() + "/src/"
        db = sqlite3.connect(path + '_database.db')
    except sqlite3.Error as error:
        print(error)
    finally:
        return db, db.cursor()

db_connection, db_cursor = connect_db()
Database.set_(db_connection, db_cursor)