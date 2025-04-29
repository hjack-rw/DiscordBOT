from datetime import datetime, timedelta
from enum import Enum

import itertools
import os
import re
import sqlite3


__all__ = ["sql_insert_delete_with_all_validator", "sql_update_one_validator", "sql_entire_table_init_validator",
           "permutation", "Filter", "Database"]


# Data conversions operations
############################################################################################################

# datetime
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

def sql_insert_delete_with_all_validator(func):
    """Validator if the table was loaded fully"""

    def validator(self, *args, **kwargs):
        if not check_variable(self, variables=["conditions", "is_shortened"]):
            return func(self, *args, **kwargs)
        
        # print error not to interrupt app
        print(f"Can only '{func.__name__}' with fully loaded table!")
    
    return validator

def sql_update_one_validator(func):
    """Validate if more than one record was loaded"""

    def validator(self, *args, **kwargs):
        if len(self.raw_data) < 2 and not check_variable(self, variables=["is_shortened"]):
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

def check_type(key, value, type, req_numeric=False):
    """Check the values in question if == type(column)"""
    
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

# Clauses
############################################################################################################

def apply_selected_columns(with_defaults=True):
    """Apply correct formatting for selected columns"""

    def run(func):
        def apply(self, *args, **kwargs):
            
            if self.is_shortened:
                kwargs["columns"] = ", ".join(self._get_imported_columns()).upper()
            else:
                kwargs["columns"] = "*"
            return func(self, *args, **kwargs)

        def apply_without_defaults(self, *args, **kwargs):
            
            custom_id = kwargs.pop("custom_id", None)

            if custom_id:
                kwargs["custom_id"] = self._return_value(custom_id, type(custom_id))
                
                kwargs["columns"] = filter(lambda item: not item[1]["has_default"], self.columns.items())
            
            # else autoiterate
            else:
                kwargs["columns"] = filter(lambda item: not item[1]["has_default"] and not item[1]["is_pk"], self.columns.items())
            return func(self, *args, **kwargs)

        if with_defaults:
            return apply
        return apply_without_defaults
    return run

class Filter(Enum):
    NONE     = ""
    STANDARD = " = *"
    BOOL_T   = "* = 1"
    BOOL_F   = "* = 0"
    NULL     = "* IS NULL" 

def apply_conditions(func):
    """Apply correct formatting for conditions"""
    
    def apply(self, *args, **kwargs):
        conditions = kwargs.pop("conditions", self.conditions)

        if conditions and (Filter.NONE not in conditions):
            clause = " AND ".join([f"{condition}" for condition in conditions])

            if "*" in clause:
                Exception(f"an error occurred while applying conditions:\n'{clause}'")
                
            kwargs["conditions"] = "WHERE " + clause
        else:
            kwargs["conditions"] = ""
        return func(self, *args, **kwargs)
    
    return apply

def apply_order(func):
    """Apply correct formatting order"""

    def apply(self, *args, **kwargs):
        kwargs["order"] = ""
        
        try:
            if self.order:
                kwargs["order"] = "ORDER BY " + ", ".join(self.order)
        except AttributeError:
            pass
        
        return func(self, *args, **kwargs)
    
    return apply

def get_update_clause(self, new_value):
    """Get update clause"""
    
    # get the record
    id, record = zip(*self.raw_data.items())
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
                    raise Exception("mismatched datatypes!")
                elif type(old_value) == permutation:
                    if not value.check():
                        raise Exception("mismatched datatypes!")
            except Exception as exception:
                print("Error: ", exception)
                value = old_value

        # convert to db value
        change = self._return_value(value, type(value))
    
        update_clause += [f"{column} = {change}"]

        record[column_id] = change
    return ", ".join(update_clause), id, record

# SQL connection
############################################################################################################

class Database():
    @classmethod
    def connect(cls):
        """Access database"""

        try:
            path = os.getcwd() + "/src/"
            db = sqlite3.connect(path + '_database.db')
        except sqlite3.Error as error:
            print(error)
        finally:
            cls.con = db
            cls.cur = db.cursor()
    
    def disconnect(cls):
        """Close database"""

        cls.cur.close()
        cls.con.close()

# Basic SQL commands
############################################################################################################

    @apply_selected_columns()
    @apply_conditions
    @apply_order
    def _select(self, table, columns, conditions, order):
        """Command SELECT"""

        # execute command
        try:
            command = f"SELECT {columns} FROM {table} {conditions} {order};"
            self.cur.execute(command)
        except sqlite3.OperationalError:
            print("Error:", command)
        
        return {row[0]:tuple(row[1:]) for row in self.cur}

    @apply_conditions
    def _update(self, conditions, new_value):
        """Command UPDATE"""

        update, id, record = get_update_clause(self, new_value)

        # execute command
        try:
            command = f"UPDATE {self.table} SET {update} {conditions};".replace("None", "NULL")
            self.cur.execute(command)
            self.con.commit()
        except sqlite3.OperationalError:
            print("Error:", command)
        
        # replace the changed value in record
        self.raw_data[id] = tuple(record)

    @apply_selected_columns(with_defaults=False)
    def _insert(self, columns, new_record, custom_id=None):
        """Command INSERT"""
        
        # protect from creating duplicates
        try:
            {value:key for key,value in self.raw_data.items()}[new_record]
            print(f"{new_record} is already in the database!")

        # if not a duplicate
        except KeyError:
            
            new_record = [self._return_value(value, type(value)) for value in new_record]

            if custom_id:
                id, values = custom_id, (custom_id, *new_record)
            else:
                id, values = self._get_last_id() + 1, new_record

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
            self.raw_data[id] = tuple(new_record)

    @apply_conditions
    def _delete(self, conditions, id):
        """Command DELETE"""

        # protect from deleting nonexistant
        try:
            record = self.raw_data[id]
            
            # execute command
            command = f"DELETE FROM {self.table} {conditions};"
            self.cur.execute(command)
            self.con.commit()
            del self.raw_data[id]
        
            # return the deleted record
            return {id: record}

        # if doesn't exitst
        except KeyError:
            print(f"no such record in the database! Error: {command}")
            return None

    def _get_columns(self, types={}, omitted_columns=[], specified_columns=[]):
        """Get column names and basic info"""
        
        types_dict = {"INTEGER":"int",
                      "REAL":   "float", 
                      "NUMERIC":"undefined", # Float or Int
                      "TEXT":   "str",
                      "BLOB":   "object"}    # Binary Large Object
        
        types_dict.update(types)

        # execute command
        self.cur.execute(f"PRAGMA table_info({self.table});")       

        columns = {}
        for (_, column_name, type, not_null, has_default, is_pk) in self.cur:

            if "+" in column_name or "-" in column_name:
                raise Exception(f"+ / - cannot appear in the column name!")

            # keep pk
            if not is_pk:
                if (specified_columns and column_name not in specified_columns) or (column_name in omitted_columns):
                    columns[column_name] = None
                    continue
            
            columns[column_name] = {"is_pk":       bool(is_pk),
                                    "type":        types_dict.pop(column_name, types_dict[type]),
                                    "not_null":    bool(not_null),
                                    "has_default": bool(has_default)}
        
        return columns

# SQL I/O
############################################################################################################

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

# Database structure
############################################################################################################

    def _setup_table(self, types={}, **kwargs):
        """Setup filters and sorting of the table"""

        omitted_columns   = kwargs.pop("omitted_columns",   [])
        specified_columns = kwargs.pop("specified_columns", [])
        order             = kwargs.pop("order",             [])

        # protect from excluding specified
        if omitted_columns in specified_columns:
            raise Exception(f"'specified_columns' and 'omitted_columns' can't overlap!")
        
        
        columns = self._get_columns(types, omitted_columns, specified_columns)
        self.is_shortened, allowed_filters = not all((columns.values())), list(filter(columns.get, columns))


        # set conditions based on the filters
        self.conditions = []
        for key, value in kwargs.items():
            
            # specification on certain variables
            try:
                key, spec = key.split("__")
            except ValueError:
                key, spec = next(iter(key.split("__"))), None
            

            if key not in allowed_filters:
                raise Exception(f"filter '{key}' can't be applied to the requested data/table!")
            
            
            type = columns[key]["type"]
            spec_is_numeric = True if spec and spec != "inequal" else False
            
            # if value has the correct type apply conditions
            if type != "bool":
                
                # int / float / undefined / datetime / binary
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
                
                # string / permutation
                else:
                    if "permutation" in type:
                        permutation = permutation(0, requirements=type.split('_'))
                        permutation.instance = value
                        value = permutation
                
                    check_type(key, value, type, req_numeric=spec_is_numeric)

                self.conditions += [key.upper() + Filter.STANDARD.value.replace("*", str(self._return_value(value, type)))]

            # bool
            elif type == "bool" and check_type(key, value, type, req_numeric=spec_is_numeric):
                value_filter = Filter.BOOL_T if value else Filter.BOOL_F
                self.conditions += [value_filter.value.replace("*", key.upper())]
            
            
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


        # set order in columns
        self.order = []
        for column in order:
            
            column_name, spec = column[:-1], column[-1]
            
            if spec not in ["+", "-"]:
                raise Exception(f"the last character has to be + / - !")
            elif column_name not in list(columns.keys()):
                raise Exception(f"the '{column_name}' does not exsit or was not loaded!")
            
            self.order += [column_name.upper() + (" ASC" if spec == "+" else " DESC")]
        
        # columns dict {"column_name":...}
        return columns

    def _get_values_from_raw_data(self, raw, add_id=False):
        """ Return the table records in a list of dict """
        
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

    def _get_type_from_column(self, value_type):
        """ Return value_type from another column if needed """
        
        if isinstance(value_type, int):
            return next(iter(self.raw_data.values()))[value_type]
        return value_type

    # TODO! Only one ID supported at the time, the first Primary Key
    def _get_id_column(self):
        return next(filter(lambda item: item[1]["is_pk"], self.columns.items()))[0]

    def _get_imported_columns(self):
        return filter(self.columns.get, self.columns)

    def _get_last_id(self):
        return int(next(iter(self._select(table="sqlite_sequence", conditions=["NAME" + Filter.STANDARD.value.replace("*", f"'{self.table}'")]).values()))[0])