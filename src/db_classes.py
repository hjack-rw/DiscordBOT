from src.db import *

import atexit
import copy


__all__ = ["ExtraVariable", "WelcomeMessages", "Portkeys"]


# Tables
############################################################################################################

class ExtraVariable(Database):
    
    @sql_entire_table_init_validator
    def __init__(self, **kwargs):
        self.table    = "extra_variables"
        self.columns  = self._setup_table(types={"value":0}, **kwargs)
        self.raw_data = self._only_one_variable(self._select(self.table))
    
    # one at the time ExtraVariable validator
    def _only_one_variable(self, raw):
        if len(raw) > 1:
            raise Exception(f"{self.table} can only be loaded one at the time!")
        elif self.is_shortened:
            raise Exception(f"{self.table} can only be loaded fully!")
        return raw

    # change the value of ExtraVariable
    def change(self, to):
        value = next(iter(self._get_values_from_raw_data(self.raw_data)))["value"]
        
        if type(value) == permutation:
            value = copy.deepcopy(value)
            value.instance = to
            to = value
        
        self._update(new_value={"value":to})

    # return ExtraVariable
    def get(self):
        value = next(iter(self._get_values_from_raw_data(self.raw_data)))["value"]
        if type(value) == permutation:
            return value.instance
        return value


class WelcomeMessages(Database):
    def __init__(self, **kwargs):
        self.table    = "welcome_messages"
        self.columns  = self._setup_table(types={"date":"datetime"}, **kwargs)
        self.raw_data = self._select(self.table)

    # add WelcomeMessage
    @sql_insert_delete_with_all_validator
    def add(self, user_id, message_id, date):
        self._insert(new_record=(message_id, date), custom_id=user_id)
    
    # remove WelcomeMessage
    @sql_insert_delete_with_all_validator
    def remove(self, user_id):
        if deleted_record := self._delete(conditions=[self._get_id_column().upper() + Filter.STANDARD.value.replace("*", str(user_id))], id=user_id):
            return next(iter(self._get_values_from_raw_data(deleted_record)))["message_id"]
        return None

    # return WelcomeMessages
    def get(self):
        return self._get_values_from_raw_data(self.raw_data, add_id=True)


class Portkeys(Database):
    def __init__(self, **kwargs):
        self.table    = "portkeys"
        self.columns  = self._setup_table(types={"from_wb":"bool", "multiple_choice":"binary_13", "birthday":"datetime"}, **kwargs)
        self.raw_data = self._select(self.table)
    
    # add Portkey
    @sql_insert_delete_with_all_validator
    def add(self, portkey):
        self._insert(new_record=portkey)
    
    # update Portkey
    @sql_update_one_validator
    def unarchive(self, message_id):
        self._update(new_value={"message_id":message_id})

    # archive Portkey
    @sql_update_one_validator
    def archive(self):
        try:
            message_id = self.get()["message_id"]
            self._update(new_value={"message_id":None})
            return message_id
        except TypeError:
            return None

    # return Portkey / Portkeys
    def get(self, multiple=False):
        if not multiple:
            try:
                return self._get_values_from_raw_data(self.raw_data, add_id=True)[0]
            except IndexError:
                return None
        return [portkey["user_id"] for portkey in self._get_values_from_raw_data(self.raw_data)]

############################################################################################################

db = Database
db.connect()
atexit.register(db.disconnect, db)