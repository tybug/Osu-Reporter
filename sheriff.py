from recorder import Recorder
import logging


class Sheriff(Recorder):
    """
    Manages successive sweeps through the reported users, to check if any are reported.
    """

    log = logging.getLogger()

    def __init__(self, DB):
        """
        Initializes a Sheriff instance.

        Args:
            DB DB: The database interface and connection for this class.
        """

        Recorder.__init__(self, DB)

    def get_records(self):
        """
        Returns recently reported users (as defined by db#get_recent_users).
        """

        return self.DB.get_recent_users()

    def get_recentish_records(self):
        return self.DB.get_recentish_users()
