from reddit_bound import RedditBound
from recorder import Recorder
import logging


class Sheriff(Recorder):
    '''
    Manages successive sweeps through the reported users, to check if any are reported
    '''

    log = logging.getLogger()

    def __init__(self, DB):
        Recorder.__init__(self, DB)

    def get_records(self):
        '''
        Returns all user records reported within LIMIT_DAYS (as defined by db#get_recent_users), and not already restricted, from the database
        '''
        return self.DB.get_recent_users()


