from config import SUB, REPLY_IGNORE
import logging
from recorder import Recorder
from reddit_bound import RedditBound
from config import REPLY_FOOTER
from parser import parse_title_data, parse_user_data, create_reply


class Report(Recorder, RedditBound):
    """
    Manages a single report submission.

    This class is used for managing reports as they come in. See OldReport for checking reports for restrictions.

    Attributes:
        Submission submission: The reddit submission.
        Boolean shouldComment: Whether comments should be left on the submission.
        Boolean shouldFlair: Whether the flair of the submission should be modified.
        DB DB: The database interface and connection for this class.
    """

    log = logging.getLogger()

    def __init__(self, submission, shouldComment, shouldFlair, DB):
        """
        Initializes a Report instance.

        Args:
            Submission submission: The reddit submission.
            Boolean shouldComment: Whether comments should be left on the submission.
            Boolean shouldFlair: Whether the flair of the submission should be modified.
            DB DB: The database interface and connection for this class.
        """

        Report.log.debug("")
        Report.log.info("Processing submission https://redd.it/" + submission.id)
        Recorder.__init__(self, DB)
        RedditBound.__init__(self, submission, shouldComment, shouldFlair)

        self.title_data = parse_title_data(self.title)

        if self.title_data is not None:
            self.gamemode = self.title_data[0]
            self.username = self.title_data[1]
            self.offense_data = self.title_data[2]
            self.flair_data = self.title_data[3]
            self.user_data = parse_user_data(self.username, self.gamemode, "string")

            if self.user_data is not None:
                self.user_id = self.user_data[0]["user_id"]

    def reply(self, message):
        """
        Replies to the reddit submission with the given message.

        Replies the message with REPLY_FOOTER appended and distinguishes that comment.

        Args:
            String message: The message to leave.
        """

        if not self.shouldComment:
            Report.log.debug(
                "Flag set; not leaving reply on post {}".format(self.submission.id)
            )
            return self

        Report.log.info("Replying to submission {}".format(self.submission.id))
        comment = self.submission.reply(message + REPLY_FOOTER)
        comment.mod.distinguish(how="yes", sticky=True)
        return self

    def reply_data_and_mark(self):
        """
        Replies to the report with the data for the reported user, including their preivous reports.
        Also adds the user to the users table to be checked for restriction.

        Also flairs the post by number of previous reports and id. Should render #flair useless (it'll get overwritten).
        """
        self.reply(
            create_reply(
                self.text,
                self.user_data,
                getattr(self, "previous_links", ""),
                self.gamemode,
            )
        )
        self.DB.add_user(
            self.post_id,
            self.user_id,
            self.submission.created_utc,
            self.offense_data[0],
            self.offense_data[1],
            self.submission.author.name,
        )

        # I think this is guaranteed to be at least 1 because we add_user'd right before
        num_previous_reports = len(self.DB.submissions_from_user(self.user_id)) - 1
        rank = int(self.user_data[0]["pp_rank"])
        rank_str = None
        # users with 0 plays have a rank of zero in the api, we don't want to
        # flair them as 100 though
        if rank == 0:
            rank_str = "infinity"
        elif rank < 100:
            rank_str = "100"
        elif rank < 1000:
            rank_str = "1k"
        elif rank < 10000:
            rank_str = "10k"
        elif rank < 50000:
            rank_str = "50k"
        elif rank < 100000:
            rank_str = "100k"
        else:
            rank_str = "infinity"
        flair = (
            rank_str
            + "-"
            + (str(num_previous_reports) if num_previous_reports <= 4 else "4-plus")
        )
        self.submission.mod.flair(flair, flair)

        return self

    def flair(self):
        if self.submission.link_flair_text == "Resolved":
            return self

        if not self.shouldFlair:
            Report.log.debug(
                "Flag set; not flairing post {} as {}".format(
                    self.post_id, self.flair_data[1]
                )
            )
            return self

        self.submission.mod.flair(self.flair_data[0], self.flair_data[1])
        return self

    def has_blacklisted_words(self):
        return [i for i in REPLY_IGNORE if i in self.title]

    def generate_previous_links(self):
        reports = self.DB.submissions_from_user(self.user_id)
        if not reports:
            return
        links = ""
        for i, report in enumerate(reports, start=1):
            links += "[[{}]]({}) | ".format(i, "https://redd.it/" + str(report[0]))
            # remove trailing pipe
        links = "All previous reports: " + links[:-2] if links else links
        self.previous_links = links
        return links

    def reject(self, reason, remove=False):
        Report.log.info("Rejecting post {} for {}".format(self.post_id, reason))
        self.DB.reject_submission(self.post_id, reason)
        if remove:
            Report.log.info("Removing post {}".format(self.post_id))
            self.submission.mod.remove()
        return self

    def mark_read(self):
        self.log.debug("marking report as read")
        self.DB.add_submission(self.post_id)
        return self

    def check_malformatted(self):
        return self.title_data is None

    def check_restricted(self):
        return self.user_data is None

    def check_duplicate(self):
        return self.DB.user_exists(self.user_id)
