
class Recorder:
    def __init__(self, db):
        '''
        Interface for objects that require a database connection to either read from or write to the database.
        '''
        self.DB = db