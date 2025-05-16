from src.db import *
from src.functions import parse_xp_amount, parse_portkey_data

import copy


__all__ = ["Experience", "ExtraVariable", "Portkeys", "WelcomeMessages"]


# Tables
############################################################################################################

class Experience(Database):
    def __init__(self, **kwargs):
        self.table    = "experience"
        self.columns  = self._setup_table(types={"offset":"bool", "archived":"bool"}, **kwargs)
        self.raw_data = self._select(self.table)
    
    # add / subtract / set Experience
    @sql_full_table_validator
    @parse_xp_amount
    @sql_update_with_valid_keys(column_names=["is_new", "user_id", "experience"])
    def tweak(self, is_new, user_id, experience):
        if is_new:
            self._insert(new_record=tuple(experience.values()), custom_id=user_id)
        else:
            self._update(conditions=self._get_conditions(id=user_id), new_value=experience, id=user_id)
        
        return experience["xp"]

    # check if record exist, soft validator
    def get_record(self, user_id):
        try:
            return next(iter(self._get_values_from_raw_data({user_id: self.raw_data[user_id]})))
        except KeyError:
            return None

    # archive Experience
    @sql_full_table_validator
    @sql_record_exisits_validator
    def archive(self, user_id):
        try:
            self._update(conditions=self._get_conditions(id=user_id), new_value={"archived":True}, id=user_id)
        except Exception:
            pass

    # change xp // level // progress for a reset  or  custom_username // offset for info cards
    @sql_full_table_validator
    @sql_record_exisits_validator(not_archived=True)
    @sql_update_with_valid_keys(column_names=["xp", "level", "progress", "username", "offset"])
    def change(self, user_id, **kwargs):
        self._update(conditions=self._get_conditions(id=user_id), new_value=kwargs, id=user_id)

    # return Experience
    def get(self):
        return self._get_values_from_raw_data(self.raw_data, add_id=True, ommit=["archived"])


class ExtraVariable(Database):
    
    @sql_entire_table_init_validator
    def __init__(self, **kwargs):  
        self.table    = "extra_variables"
        self.columns  = self._setup_table(types={"value":0}, **kwargs)
        self.raw_data = self._only_one_variable(self._select(self.table))
    
    # one at the time ExtraVariable validator
    def _only_one_variable(self, raw):
        if len(raw) > 1:
            raise Exception(f"{self.table} can only be loaded one at the time")
        elif self.is_shortened:
            raise Exception(f"{self.table} can only be loaded fully")
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


class Portkeys(Database):
    def __init__(self, **kwargs):
        self.table    = "portkeys"
        self.columns  = self._setup_table(types={"from_wb":"bool", "multiple_choice":"binary_13", "birthday":"datetime"}, **kwargs)
        self.raw_data = self._select(self.table)
    
    # add Portkey
    @sql_full_table_validator
    @parse_portkey_data
    @sql_update_with_valid_keys(column_names=["portkey"])
    def add(self, portkey):
        self._insert(new_record=portkey)
    
    # update Portkey
    @sql_only_one_validator
    @sql_update_with_valid_keys(column_names=["message_id"])
    def unarchive(self, **kwargs):
        self._update(new_value=kwargs)

    # archive Portkey
    @sql_only_one_validator
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
                return self._get_values_from_raw_data(self.raw_data, add_id=True, ommit=["message_id"])[0]
            except IndexError:
                return None
        return [portkey["user_id"] for portkey in self._get_values_from_raw_data(self.raw_data)]


class WelcomeMessages(Database):
    def __init__(self, **kwargs):  
        self.table    = "welcome_messages"
        self.columns  = self._setup_table(types={"date":"datetime"}, **kwargs)
        self.raw_data = self._select(self.table)

    # add WelcomeMessage
    @sql_full_table_validator
    def add(self, user_id, message_id, date):
        self._insert(new_record=(message_id, date), custom_id=user_id)
    
    # remove WelcomeMessage
    @sql_full_table_validator
    def remove(self, user_id):
        try:
            if deleted_record := self._delete(conditions=self._get_conditions(id=user_id), id=user_id):
                return next(iter(self._get_values_from_raw_data(deleted_record)))["message_id"]
        except Exception:
            return None

    # return WelcomeMessages
    def get(self):
        return self._get_values_from_raw_data(self.raw_data, add_id=True, ommit=["date"])