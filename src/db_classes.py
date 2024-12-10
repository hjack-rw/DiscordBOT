from src.variables import db_connection, db_cursor

__all__ = ["ExtraVariables"]


class ExtraVariables:
    
    def __init__(self, id):
        self.cur.execute(f"SELECT * FROM extra_variables WHERE ID = {id}")
        self.id, self.name, var_int = [item for item in self.cur][0]
        self.value = self.get_value(var_int)
    
    @classmethod
    def set_(cls, db_connection, db_cursor):
        cls.con = db_connection
        cls.cur = db_cursor

    def get_value(self, variable_int):

        if self.id == 1:
            return bool(variable_int)

    def change_value(self, new_value=None):
        
        # reverse value
        if self.id == 1:
            self.cur.execute(f"UPDATE extra_variables SET var_int = {int(not self.value)} WHERE ID = {self.id}")
            self.value = not self.value
        
        self.con.commit()


ExtraVariables.set_(db_connection, db_cursor)