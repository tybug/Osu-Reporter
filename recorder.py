class Recorder:
    """
    Interface for objects that require a database connection to either read from or write to the database.
    """

    def __init__(self, db):
        """
        Initializes a Recorder instance.

        Args:
            DB db: An instance of the db class.
        """

        self.DB = db
