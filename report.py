from config import SUB, REPLY_IGNORE
import logging
from recorder import Recorder
from reddit_bound import RedditBound
from config import REPLY_FOOTER
from parser import parse_title_data, parse_user_data, create_reply

class Report(Recorder, RedditBound):
    '''
    Manages a single report submission

    This class is used for managing reports as they come in. See OldReport for checking reports for restrictions
    '''

    log = logging.getLogger()


    def __init__(self, submission, shouldComment, shouldFlair, DB):
        '''
        
        :param Submission submission: The reddit submission 
        :param boolean shouldComment: Whether comments should be left on the submission
        :param boolean shouldFlair: Whether the submission's flair should be modified
        :param DB DB: The database interface and connection for this class
        '''



        Report.log.debug("")
        Report.log.info("Processing submission https://redd.it/" + submission.id)
        Recorder.__init__(self, DB)
        RedditBound.__init__(self, submission, shouldComment, shouldFlair)

        self.title_data = parse_title_data(self.title)

        if(self.title_data is not None):
            self.gamemode = self.title_data[0]
            self.username = self.title_data[1]
            self.offense_data = self.title_data[2]
            self.flair_data = self.title_data[3]
            self.user_data = parse_user_data(self.username, self.gamemode, "string")

            if(self.user_data is not None):
                self.user_id = self.user_data[0]["user_id"]


    def reply(self, message):
        if(not self.shouldComment):
            Report.log.debug("Flag set; not leaving reply on post {}".format(self.submission.id))
            return self

        Report.log.info("Replying to submission {}".format(self.submission.id))
        comment = self.submission.reply(message + REPLY_FOOTER)
        comment.mod.distinguish(how="yes", sticky=True)
        return self


    def reply_data_and_mark(self):
        '''
        Replies to the report with the data for the reported user, including their preivous reports.
        Also adds the user to the users table to be checked for restriction.
        '''
        self.reply(create_reply(self.user_data, getattr(self, "previous_links", ""), self.gamemode))
        self.DB.add_user(self.post_id, self.user_id, self.submission.created_utc, self.offense_data[0], self.offense_data[1], self.submission.author.name)
        return self


    def flair(self):
        if(self.submission.link_flair_text == "Resolved"):
            return self

        if(not self.shouldFlair):
            Report.log.debug("Flag set; not flairing post {} as {}".format(self.post_id, self.flair_data[1]))
            return self

        self.submission.mod.flair(self.flair_data[0], self.flair_data[1])
        return self
        

    def has_blacklisted_words(self):
        return [i for i in REPLY_IGNORE if i in self.title]


    def generate_previous_links(self):
        reports = self.DB.submissions_from_user(self.user_id)
        if(not reports):
            return
        links = ""
        for i, report in enumerate(reports, start=1):
            links += "[{}]({}) | ".format(i, "https://redd.it/" + str(report[0]))
        
        links = "All previous reports: " + links[:-2] if links else links
        self.previous_links = links
        return links # remove trailing pipe


    def reject(self, reason):
        Report.log.info("Rejecting post {} for {}".format(self.post_id, reason))        
        self.DB.reject_submission(self.post_id, True, reason)
        return self


    def mark_read(self):
        self.DB.add_submission(self.post_id)
        return self


    def check_malformatted(self):
        return (self.title_data is None)


    def check_restricted(self):
        return (self.user_data is None)

    
    def check_duplicate(self):
        return self.DB.user_exists(self.user_id)
