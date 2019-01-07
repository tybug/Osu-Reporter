from reddit_bound import RedditBound
from parser import parse_user_data
import logging
from recorder import Recorder
import time


class OldReport(Recorder, RedditBound):
    """
    Manages a previously submitted report

    Used to check the previously submitted report for restrictions. See Report for managing submissions as they come in
    """

    log = logging.getLogger()

    def __init__(self, submission, shouldComment, shouldFlair, record, DB):
        Recorder.__init__(self, DB)
        RedditBound.__init__(self, submission, shouldComment, shouldFlair)

        self.user_id = record[0] # user id
        self.post_date = int(float(record[2])) # post submission date, convert from string to int
        self.offense_type = record[3]
        self.blatant = record[4]
        self.reportee = record[5]

    def check_restricted(self):
        try:
            user_data = parse_user_data(self.user_id, "0", "id")    # gamemode doesn't matter here since we're just
                                                                    # checking for empty response
        except Exception as e:
            OldReport.log.warning("Exception while parsing user data for user {}: {}".format(self.user_id, str(e)))
            return True
            
        return True if not user_data else False

    def get_user_records(self):
        return self.DB.submissions_from_user(self.user_id)

    def resolve(self):
        """
        Flairs the submission tied to the OldReport as resolved and marks the entry with the OldReport's post id as restricted in the db

        If shouldFlair is set the post is not flaired
        """
        if(self.shouldFlair):
            self.submission.mod.flair("Resolved", "resolved")
        
        self.DB.restrict_user(self.post_id, time.time())
        self.DB.restrict_submission(self.post_id)
