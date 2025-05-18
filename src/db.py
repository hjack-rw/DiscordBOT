from datetime import datetime, timedelta
from enum import Enum

import functools
import inspect
import io
import itertools
import os
import sqlite3


__all__ = ["sql_full_table_validator", "sql_only_one_validator", "sql_update_with_valid_keys", "sql_record_exisits_validator", "sql_entire_table_init_validator",
           "sql_create_connection", "permutation", "Filter", "Database"]


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

def sql_full_table_validator(func):
    """Validator if the table was loaded fully"""

    @functools.wraps(func)
    def validator(self, *args, **kwargs):
        if not check_variable(self, variables=["conditions", "is_shortened", "extended"]):
            return func(self, *args, **kwargs)
        
        raise Exception(f"sqlite3 table error: can only '{func.__name__}' with fully loaded table")
    
    return validator

def sql_only_one_validator(func):
    """Validate if more than one record was loaded"""

    @functools.wraps(func)
    def validator(self, *args, **kwargs):
        if len(self.raw_data) == 1 and not check_variable(self, variables=["is_shortened", "extended"]):
            return func(self, *args, **kwargs)
        
        raise Exception(f"sqlite3 table error: can only '{func.__name__}' with one record loaded")
    
    return validator

def sql_update_with_valid_keys(column_names):
    """Validate if keys used to update are valid"""

    def run(func):
        @functools.wraps(func)
        def validator(self, *args, **kwargs):
            valid_keys = [self._get_id_column(), *column_names]
            invalid_keys = [key for key in kwargs if key not in valid_keys]
            if invalid_keys:
                raise ValueError(f"sqlite3 table error: invalid columns in kwargs: {invalid_keys}")
            
            return func(self, *args, **kwargs)
        return validator
    return run

def sql_record_exisits_validator(not_archived=False):
    """Validate if record exisits in the loaded data"""

    def run(func):
        @functools.wraps(func)
        def validator(self, *args, **kwargs):
            try:
                column_id = self._get_id_column()
                record = {kwargs[column_id]: self.raw_data[kwargs[column_id]]}
                
                if not_archived:
                    if next(iter(self._get_values_from_raw_data(record)))["archived"]:
                        raise Exception(f"sqlite3 table error: the {column_id.upper()} in question is ARCHIVED")
                return func(self, *args, **kwargs)
            except KeyError:
                raise Exception(f"sqlite3 table error: no such record in the database")
        return validator
    return run

def sql_entire_table_init_validator(func):
    """Validator for tables that need all rows loaded"""

    @functools.wraps(func)
    def validator(self, *args, **kwargs):
        for kwarg in kwargs:
            if kwarg in ["omitted_columns", "specified_columns"]:
                raise Exception(f"sqlite3 table error: needs to load all rows for '{self.__name__}'")
        return func(self, *args, **kwargs)
    
    return validator

def check_type(key, value, type, req_numeric=False):
    """Check the values in question if == type(column)"""
    
    try:
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
            type_dict = {"int":int,"float":float,"str":str,"datetime":datetime, "bool":bool}
            
            if not isinstance(value, type_dict[type]):
                raise Exception(f"'{key}' is not a {type}!")
        
        if req_numeric:
            raise Exception(f"'{key}' has not a numeric filter!")
    except Exception as error:
        raise Exception(f"sqlite3 filter error: {str(error)}")
    
    return True

# Decorators
############################################################################################################

def sql_create_connection(func):
    """Create linked table record"""

    @functools.wraps(func)
    def decorator(self, *args, **kwargs):
        is_new = kwargs.get("is_new", False)
        result = func(self, *args, **kwargs)

        # if the main table is new
        if is_new:
            
            # check if linked record already exsits
            column_id = self._get_id_column()
            if self.get_joined_table(**{column_id:kwargs[column_id]}) is None:

                # create a new kwargs with the gotten key-value pairs
                needed_kwargs = {param.name: kwargs.get(param.name) for param in inspect.signature(self.joined_table.add).parameters.values() if param.name != "self"}

                try:
                    missing_params = [key for key,value in needed_kwargs.items() if value is None]

                    # not enough parameters provided
                    if missing_params:
                        raise Exception("missing required parameters: " + ", ".join(missing_params))

                    self.joined_table().add(**needed_kwargs)
                except Exception as error:
                    raise Exception(f"sqlite3 table error: failed to create a link with '{self._get_joined_table_name()}' for '{self.__class__.__name__}'\n Error:{str(error)}")

        return result
    return decorator

# Clauses
############################################################################################################

def apply_selected_columns(skip_when_default=False):
    """Apply correct formatting for selected columns"""

    def run(func):
        def apply(self, *args, **kwargs):
            
            if self.is_shortened:
                kwargs["columns"] = ", ".join(self._get_imported_columns()).upper()
            else:
                kwargs["columns"] = "*"
            return func(self, *args, **kwargs)

        def apply_skip_when_default(self, *args, **kwargs):
            
            custom_id = kwargs.pop("custom_id", None)

            if custom_id:
                kwargs["custom_id"] = self._return_value(custom_id, type(custom_id))
                
                kwargs["columns"] = filter(lambda item: not item[1]["default"], self.columns.items())
            
            # else autoiterate
            else:
                kwargs["columns"] = filter(lambda item: not item[1]["default"] and not item[1]["is_pk"], self.columns.items())
            return func(self, *args, **kwargs)

        if skip_when_default:
            return apply_skip_when_default
        return apply
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
                raise Exception(f"sqlite3 error applying conditions:\n'{clause}'")
                
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

def get_update_clause(self, new_value, id=None):
    """Get update clause"""

    try:
        # get the only loaded record
        if id is None:
            if len(self.raw_data) != 1:
                raise Exception(f"for more than 1 record loaded ID has to be provided")
            
            id, record = next(iter(self.raw_data.items()))
        
        # get the record by id
        else:
            record = self.raw_data[id]

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
            if not_null and value is not None:
                if type(old_value) != type(value):
                    raise Exception(f"datatype mismatch for column '{column}'")
                if isinstance(old_value, permutation) and not value.check():
                    raise Exception(f"invalid permutation object for column '{column}'")

            # convert to db value
            change = self._return_value(value, type(value))
        
            update_clause.append(f"{column} = {change}")

            record[column_id] = change
        return ", ".join(update_clause), id, record
    
    except Exception as exception:
        raise Exception(f"sqlite3 UPDATE clause error: {str(exception)}")

# SQL connection
############################################################################################################

class Database():
    database_path = os.getcwd() + "/src/"
    database_name = "__database__.db"
        
    con = None
    cur = None

    @classmethod
    def connect(cls):
        """CONNECT database"""

        try:
            cls.con = sqlite3.connect(cls.database_path + cls.database_name)
            cls.cur = cls.con.cursor()
        except sqlite3.Error as error:
            raise Exception(f"sqlite3 CONNECT error: {str(error)}!")
    
    @classmethod
    def disconnect(cls):
        """CLOSE database"""

        if cls.cur:
            cls.cur.close()
        
        if cls.con:
            cls.con.close()

    @classmethod
    def backup(cls):
        """BACKUP database to a dump file"""

        if cls.con:
            with io.open(file=cls.database_path + f"{cls.database_name}-dump", mode="w", encoding="utf-8") as file: 
            
                # iterdump() function
                for line in cls.con.iterdump():
                    file.write('%s\n' % line)
        else:
            raise Exception("sqlite3 BACKUP error: no active database connection to back up!")
    
    @classmethod
    def restore(cls):
        """Restore database from a dump file"""

        with open(file=cls.database_path + f"{cls.database_name}-dump", mode="r", encoding="utf-8") as file:
            sql_script = file.read()

        cls.con.executescript(sql_script)
        cls.con.commit()

# Basic SQL commands
############################################################################################################

    @apply_selected_columns()
    @apply_conditions
    @apply_order
    def _select(self, table, columns, conditions, order):
        """Command SELECT"""

        join = ""

        # check if the table has been extended
        if getattr(self, "extended", False):
            id_column = self._get_id_column()
            join = f"INNER JOIN {self._get_joined_table_name()} USING ({id_column})"

        # execute command
        try:
            command = f"SELECT {columns} FROM {table} {join} {conditions} {order};"
            self.cur.execute(command)
        except sqlite3.OperationalError:
            raise Exception(f"sqlite3 SELECT error! faulty command:\n'{command}'")
        
        return {row[0]:tuple(row[1:]) for row in self.cur}

    @apply_conditions
    def _update(self, conditions, new_value, id=None):
        """Command UPDATE"""

        update, id, record = get_update_clause(self, new_value, id)

        # execute command
        try:
            command = f"UPDATE {self.table} SET {update} {conditions};".replace("None", "NULL")
            self.cur.execute(command)
            self.con.commit()
        except sqlite3.OperationalError:
            raise Exception(f"sqlite3 UPDATE error! faulty command:\n'{command}'")
        
        # replace the changed value in record
        self.raw_data[id] = tuple(record)

    @apply_selected_columns(skip_when_default=True)
    def _insert(self, columns, new_record, custom_id=None):
        """Command INSERT"""
        
        # insert the new record, but add in default values
        idx, new_record_with_defaults = 0, []
        for column, meta in self.columns.items():
            if meta["is_pk"]:
                continue
            
            default = meta["default"]
            if default is not None:
                new_record_with_defaults.append(None if default == 'NULL' else default)
            else:
                new_record_with_defaults.append(new_record[idx])
                idx += 1

        # protect from creating duplicates
        if new_record_with_defaults in self.raw_data.values():
            raise Exception(f"sqlite3 INSERT error: {new_record} is already in the database")

        # if not a duplicate
        sql_values = [self._return_value(value, type(value)) for value in new_record]

        if custom_id is None:
            id = self._get_last_id() + 1
        else:
            id, sql_values = custom_id, (custom_id, *sql_values)

        columns = ", ".join([column for column,_ in columns]).upper()
        values  = ", ".join([str(value) for value in sql_values])

        # execute command
        try:
            command = f"INSERT INTO {self.table} ({columns}) VALUES ({values});".replace("None", "NULL")
            self.cur.execute(command)
            self.con.commit()
        except sqlite3.IntegrityError:
            raise Exception(f"sqlite3 INSERT error: failed to add to the database! command:\n'{command}'")

        self.raw_data[id] = tuple(new_record_with_defaults)

    @apply_conditions
    def _delete(self, conditions, id):
        """Command DELETE"""

        # protect from deleting nonexistant
        try:
            command = f"DELETE FROM {self.table} {conditions};"
            record = self.raw_data[id]
            
            # execute command
            self.cur.execute(command)
            self.con.commit()
            del self.raw_data[id]
        
            # return the deleted record
            return {id: record}

        # if doesn't exitst
        except KeyError:
            raise Exception(f"sqlite3 DELETE error: no such record in the database! command:\n'{command}'")

    def _get_columns(self, types={}, omitted_columns=[], specified_columns=[]):
        """Get column names and basic info"""
        
        types_dict = {"INTEGER":"int",
                      "REAL":   "float", 
                      "NUMERIC":"undefined", # Float or Int
                      "TEXT":   "str",
                      "BLOB":   "object"}    # Binary Large Object
        
        types_dict.update(types)

        # execute commands
        self.cur.execute(f"PRAGMA table_info({self.table});")
        columns = self.cur.fetchall()

        # extended the columns with the joined_table
        if getattr(self, "extended", False):
            self.cur.execute(f"PRAGMA table_info({self._get_joined_table_name()});")
            columns_origin = self.cur.fetchall()
        else:
            columns_origin = []

        all_columns = {}
        for (_, column_name, type, not_null, default, is_pk) in columns + columns_origin:

            if "+" in column_name or "-" in column_name:
                raise Exception(f"sqlite3 table error: '+' / '-' cannot appear in the column name!")

            # skip redefinition if already processed
            if column_name in all_columns:
                continue

            # keep pk
            if not is_pk:
                if (specified_columns and column_name not in specified_columns) or (column_name in omitted_columns):
                    all_columns[column_name] = None
                    continue
            
            all_columns[column_name] = {"is_pk":       bool(is_pk),
                                        "type":        types_dict.pop(column_name, types_dict[type]),
                                        "not_null":    bool(not_null),
                                        "default":     default}
        
        return all_columns

# SQL I/O
############################################################################################################

    def _get_value(self, value, type):
        """ Convert out of DB value """

        if type == "bool":
            return bool(value)
        elif type == "datetime":
            return convert_int_to_date(value)
        elif "binary" in type:
            return ('{0:0' + type.split("_")[1] + 'b}').format(value)
        elif type == "str":
            if value:
                return value.replace("`", "'")
        elif "permutation" in type:
            return permutation(value, requirements=type.split('_'))
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
        elif type in ["binary", "str"]: 
            if is_binary(value):
                value = int(value, 2)
            else:
                return "'" + value.replace("'", "`") + "'"
        elif type == "permutation":
            value = value.convert_permutation_to_int()
        return value

# Database structure
############################################################################################################

    @classmethod
    def get_joined_table(cls, get_kwargs=None, **kwargs):
        get_kwargs = get_kwargs or {}
        return cls.joined_table(**kwargs).get(**get_kwargs)

    def _setup_table(self, types={}, **kwargs):
        """Setup filters and sorting of the table"""

        omitted_columns   = kwargs.pop("omitted_columns",   [])
        specified_columns = kwargs.pop("specified_columns", [])
        order             = kwargs.pop("order",             [])

        # protect from excluding specified
        if omitted_columns in specified_columns:
            raise Exception(f"sqlite3 filter error: 'specified_columns' and 'omitted_columns' can't overlap!")
        
        
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
                raise Exception(f"sqlite3 filter error: filter '{key}' can't be applied to the requested data/table!")
            
            
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
                            self.conditions.append(Filter.NULL.value.replace("*", key.upper()))
                        
                            if value == "unarchived":
                                self.conditions[-1] = self.conditions[-1].replace("IS", "IS NOT")
                            
                            continue
                        
                        elif isinstance(value, str):
                            raise Exception(f"sqlite3 filter error: '{value}' is not an accepted keyword!")

                    check_type(key, value, type)
                
                # string / permutation
                else:
                    if "permutation" in type:
                        permutation = permutation(0, requirements=type.split('_'))
                        permutation.instance = value
                        value = permutation
                
                    check_type(key, value, type, req_numeric=spec_is_numeric)

                self.conditions.append(key.upper() + Filter.STANDARD.value.replace("*", str(self._return_value(value, type))))

            # bool
            elif type == "bool" and check_type(key, value, type, req_numeric=spec_is_numeric):
                value_filter = Filter.BOOL_T if value else Filter.BOOL_F
                self.conditions.append(value_filter.value.replace("*", key.upper()))
            
            
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
                raise Exception(f"sqlite3 order error: the last character has to be '+' / '-' !")
            elif column_name not in list(columns.keys()):
                raise Exception(f"sqlite3 order error: the '{column_name}' does not exsit or was not loaded!")
            
            self.order.append(column_name.upper() + (" ASC" if spec == "+" else " DESC"))
        
        # columns dict {"column_name":...}
        return columns

    def _get_values_from_raw_data(self, raw, add_id=False, omitted=[], specified=[]):
        """ Return the table records in a list of dict """
        
        # protect from excluding specified
        if omitted in specified:
            raise Exception(f"sqlite3 filter error: 'specified' and 'omitted' can't overlap!")

        return_list = []
        for idx, instance in raw.items():
            temp_dict = {}
            
            for idx_column, column in enumerate(self._get_imported_columns(), -1):
                is_pk , value_type, _, _  = self.columns[column].values()
                
                if is_pk:
                    if add_id:
                        temp_dict[column] = idx
                    continue

                if (specified and column not in specified) or (column in omitted):
                    continue

                temp_dict[column] = self._get_value(instance[idx_column], self._get_type_from_column(value_type))
            
            return_list.append(temp_dict)
        
        return return_list

    def _get_type_from_column(self, value_type):
        """ Return value_type from another column if needed """
        
        if isinstance(value_type, int):
            return next(iter(self.raw_data.values()))[value_type]
        return value_type

    #NOTE! only one ID supported at the time, the first Primary Key
    def _get_id_column(self):
        return next(filter(lambda item: item[1]["is_pk"], self.columns.items()))[0]

    def _get_imported_columns(self):
        return filter(self.columns.get, self.columns)

    def _get_last_id(self):
        return int(next(iter(self._select(table="sqlite_sequence", conditions=["NAME" + Filter.STANDARD.value.replace("*", f"'{self.table}'")]).values()))[0])
    
    def _get_conditions(self, id):
        return [self._get_id_column().upper() + Filter.STANDARD.value.replace("*", str(id))]
    
    @classmethod
    def _get_joined_table_name(cls):
        return cls.joined_table.__name__.lower()