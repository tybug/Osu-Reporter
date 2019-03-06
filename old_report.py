from reddit_bound import RedditBound
from parser import parse_user_data
import logging
from recorder import Recorder
import time



import requests
from config import API_BASE
from secret import KEY

class OldReport(Recorder, RedditBound):
    """
    Manages a previously submitted report.

    Used to check the previously submitted report for restrictions. See Report for managing submissions as they come in.

    Attributes:
        Submission submission: The reddit submission to check.
        Boolean shouldComment: Whether comments should be left on the submission.
        Boolean shouldFlair: Whether the flair of the submission should be modified.
        DB DB: The database interface and connection for this class.
        String user_id: The id of the user reported by the submission.
        String post_date: The unix timestamp the submission was processed.
        String offense_type: What the user was reported for.
        Boolean blatant: Whether the report called the cheats blatant or not.
        String reportee: The reddit username of the reportee (not including the "u/").
    """

    log = logging.getLogger()

    def __init__(self, submission, shouldComment, shouldFlair, record, DB):
        """
        Initializes an OldReport instance.

        Args:
            Submission submission: The reddit submission to check.
            Boolean shouldComment: Whether comments should be left on the submission.
            Boolean shouldFlair: Whether the flair of the submission should be modified.
            List record: The list returned by db#get_recent_users.
            DB DB: The database interface and connection for this class.
        """

        Recorder.__init__(self, DB)
        RedditBound.__init__(self, submission, shouldComment, shouldFlair)

        self.user_id = record[1] # user id
        self.post_date = int(float(record[2])) # post submission date, convert from string to int
        self.offense_type = record[3]
        self.blatant = record[4]
        self.reportee = record[5]

    def check_restricted(self):
        """
        Checks if the user reported in the submission is restricted.

        Attempts to retrive the user's information through the api.
        If the api returns an empty response or throws an error, returns True, else returns False.
        """

        user_data = None
        try:
            user_data = parse_user_data(self.user_id, "0", "id")    # gamemode doesn't matter here since we're just
                                                                    # checking for empty response
        except Exception as e:
            log = requests.get(API_BASE + "get_user?k=" + KEY + "&u=" + self.user_id + "&m=" + "0" + "&type=" + "id").json()
            OldReport.log.warning("Exception while parsing user data for user {}: {}. Log: {}".format(self.user_id, str(e), log))
            return False

        return True if not user_data else False

    def get_user_records(self):
        """
        Retrieves information about all recent reported users.

        See db#submissions_from_user for specific implementation.
        """

        return self.DB.submissions_from_user(self.user_id)

    def resolve(self):
        """
        Flairs the submission resolved and marks its database entry as restricted
        """

        if(self.shouldFlair):
            self.submission.mod.flair("Resolved", "resolved")

        self.DB.restrict_user(self.post_id, time.time())
        self.DB.restrict_submission(self.post_id)
