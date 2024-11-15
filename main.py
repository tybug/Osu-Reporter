import argparse
import logging
import time
import threading
from prawcore.exceptions import RequestException, ServerError, ResponseException
import sys
import json
import stats
import praw
import secret
import re
from db import DB
import datetime
from report import Report
from sheriff import Sheriff
from old_report import OldReport
from config import (
    VERSION,
    SUB,
    LIMIT_DAYS,
    API_USERS,
    CHECK_INTERVAL,
    AUTHOR,
    REJECT_BLACKLISTED,
    REJECT_MALFORMATTED,
    REJECT_REPORTED,
    REJECT_RESTRICTED,
    REPLY_MALFORMATTED,
    REPLY_REPORTED,
    REPLY_RESTRICTED,
)


parser = argparse.ArgumentParser()
parser.add_argument(
    "-c", "--comment", help="doesn't leave comments on submissions", action="store_true"
)
parser.add_argument(
    "-f",
    "--flair",
    help="leaves flairs unmodified. No effect when set with --sweep",
    action="store_true",
)
parser.add_argument(
    "-d",
    "--debug",
    help="runs in debug mode. Equivelant to -cfv --leadless",
    action="store_true",
)
parser.add_argument(
    "-p", "--from-id", help="processes a single post from given id", dest="post_id"
)
parser.add_argument(
    "--leadless", help="doesn't modify the database while running", action="store_true"
)
# parser.add_argument("-t", "--test", help="runs test suite and exits", action="store_true")

g1 = parser.add_mutually_exclusive_group()
g1.add_argument(
    "--stats",
    help="calculates and displays statistics from the db",
    action="store_true",
)
g1.add_argument(
    "--sweep",
    help="runs through the past 100 submissions and flairs them appropriately, ignoring resolved threads. Sets --comment as well.",
    action="store_true",
)


g2 = parser.add_mutually_exclusive_group()
g2.add_argument("-v", "--verbose", help="enables detailed logging", action="store_true")
g2.add_argument("-s", "--silent", help="disables all logging", action="store_true")

args = parser.parse_args()

# if args.test:
# 	test_module.run()
# 	sys.exit()

if args.debug:
    args.verbose = True
    args.comment = True
    args.flair = True
    args.leadless = True

if args.sweep:
    args.comment = True


log_level = 20  # INFO
if args.verbose:
    log_level = 10  # DEBUG


log = logging.getLogger()
log.setLevel(log_level)

formatter = logging.Formatter(
    fmt="[%(levelname)s] %(asctime)s %(message)s", datefmt="%Y/%m/%d %I:%M:%S %p"
)
handler_stream = logging.StreamHandler()
handler_file = logging.FileHandler("action.log")

handler_stream.setFormatter(formatter)
handler_file.setFormatter(formatter)

log.addHandler(handler_stream)
log.addHandler(handler_file)


# Disable annoying html request logging
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("prawcore").setLevel(logging.WARNING)


if args.silent:
    logging.disable()


log.info("Logging into reddit")
# keep reddit global
reddit = praw.Reddit(
    client_id=secret.ID,
    client_secret=secret.SECRET,
    user_agent="linux:com.tybug.osureporter:v" + VERSION + " (by /u/tybug2)",
    username=secret.USERNAME,
    password=secret.PASSWORD,
)

# db interface with a single connection and cursor. Only create this once to limit connections, then pass it to each recorder object (reports and sheriffs)
DB_MAIN = DB(args.leadless)

log.info("Login successful")

# submission = praw.models.Submission(reddit, id="fw74zf")
# print(submission.link_flair_text)
# flair = submission.link_flair_text + "-resolved"
# submission.mod.flair("infinity-1", "infinity-1")
# sys.exit()


def main():

    if args.sweep:
        sweep()
        sys.exit(0)

    if args.stats:
        stats.main()
        sys.exit(0)

    if args.post_id:
        log.debug("Processing single submission {}".format(args.post_id))
        process_submission(
            praw.models.Submission(reddit, id=args.post_id),
            not args.comment,
            not args.flair,
        )
        sys.exit(0)

    try:
        check_banned(
            not args.comment, not args.flair
        )  # repeats on CHECK_INTERVAL minutes interval
    except KeyboardInterrupt:
        log.info("Received SIGINT, terminating")
        sys.exit(0)

    # Iterate over every new submission forever
    while True:

        subreddit = reddit.subreddit(SUB)
        submission_stream = subreddit.stream.submissions()
        # two layers of exception handling, one for the processing and one for the submission stream
        try:
            for submission in submission_stream:
                try:
                    # Already processed; praw returns the past 100 results for streams, previously iterated over or not
                    if DB_MAIN.submission_exists(submission.id):
                        log.debug(
                            "Submission {} is already processed".format(submission.id)
                        )
                        continue
                    process_submission(submission, not args.comment, not args.flair)
                except RequestException as e:
                    log.warning(
                        "Request exception while processing submission {}: {}. Waiting 10 seconds".format(
                            submission.id, str(e)
                        )
                    )
                    time.sleep(10)
                except ServerError as e:
                    log.warning(
                        "Server error while processing submission {}: {}. Reddit likely under heavy load".format(
                            submission.id, str(e)
                        )
                    )
                except json.decoder.JSONDecodeError as e:
                    log.warning(
                        "JSONDecode exception while processing submission {}: {}.".format(
                            submission.id, str(e)
                        )
                    )
                except Exception as e:
                    log.critical(
                        "some other error while processing submission {}: {}".format(
                            submission.id, str(e)
                        )
                    )

        except KeyboardInterrupt:
            log.info("Received SIGINT, terminating")
            sys.exit(0)
        except RequestException as e:
            log.warning(
                "Request exception in submission stream: {}. Waiting 10 seconds".format(
                    str(e)
                )
            )
            time.sleep(10)
        except ServerError as e:
            log.warning("Server error in submission stream: {}.".format(str(e)))
        except json.decoder.JSONDecodeError as e:
            log.warning("JSONDecode exception in submission stream: {}.".format(str(e)))
        except Exception as e:
            log.critical("some other error in submission stream: {}".format(str(e)))

        # sleep for two minutes, give any connection issues some time to resolve itself
        time.sleep(60 * 2)


def process_submission(submission, shouldComment, shouldFlair):
    """
    Processes the given reddit submission.
    """

    report = Report(submission, shouldComment, shouldFlair, DB_MAIN)
    report.mark_read()

    # for discssion threads etc
    if report.has_blacklisted_words():
        report.reject(REJECT_BLACKLISTED)
        return

    # title wasn't properly formatted
    if report.check_malformatted():
        report.reply(REPLY_MALFORMATTED).reject(REJECT_MALFORMATTED, remove=True)
        return

    # flair it based on what was in the title
    report.flair()

    # api gives empty json - possible misspelling or user was already restricted
    if report.check_restricted():
        report.reply(REPLY_RESTRICTED.format(API_USERS + report.username)).reject(
            REJECT_RESTRICTED, remove=True
        )
        return

    previous_links = report.generate_previous_links()

    previous_id = report.check_duplicate()  # returns post id from db query

    # If the previous submission says removed, the author likely deleted it and no one gains anything by the bot
    # linking back there. We still want to preserve any potential history in the thread so we don't modify its
    # database entry so we can still link to it in "all previous reports: "
    if previous_id and reddit.submission(id=previous_id).selftext != "[deleted]":
        log.debug(
            "User reported in post {} was already reported in the past {} days in post {}".format(
                report.post_id, LIMIT_DAYS, previous_id
            )
        )
        report.reply(
            REPLY_REPORTED.format(
                API_USERS + report.user_id,
                "https://redd.it/" + str(previous_id),
                previous_links,
                LIMIT_DAYS,
            )
        ).reject(REJECT_REPORTED)
        return

    # all special cases handled, finally reply with the data and add to db for sheriff to check
    report.reply_data_and_mark()


checked_times = 0


def check_banned(shouldComment, shouldFlair):
    thread = threading.Timer(
        CHECK_INTERVAL * 60, check_banned, [shouldComment, shouldFlair]
    )
    thread.daemon = True  # Dies when the main thread dies
    thread.start()
    global checked_times
    checked_times += 1

    try:
        # make a new one for every thread so we don't get two threads modifying at the same time
        # generating a new connection every CHECK_INTERVAL minutes isn't terribly expensive
        DB_CHECK = DB(args.leadless)
        sheriff = Sheriff(DB_CHECK)

        records = sheriff.get_records()

        # check all recentish records instead
        # occurs roughly once a day with a check interval of 15 minutes
        if checked_times % 100 == 0:
            records = sheriff.get_recentish_records()
            log.debug("checking recentish records")

        log.debug("")
        log.debug("Checking " + str(len(records)) + " posts for restrictions")
        for record in records:  # only retrieves records in the past month
            post_id = record[0]
            log.debug("Checking post {}".format(post_id))
            submission = reddit.submission(id=post_id)
            report = OldReport(submission, shouldComment, shouldFlair, record, DB_CHECK)

            if report.check_restricted():
                # resolve the original post (the one we checked)
                log.info("resolving post {}".format(report.post_id))
                report.resolve()
                # resolve all previous reports on the same guy, regardless of time limit
                for _record in report.get_user_records():
                    _report = OldReport(
                        reddit.submission(id=_record[0]),
                        shouldComment,
                        shouldFlair,
                        _record,
                        DB_CHECK,
                    )
                    _report.resolve()

        log.debug("Done. Checking mail")
        # Might as well forward pms here...already have an automated function, why not?
        for message in reddit.inbox.unread():
            isComment = isinstance(message, praw.models.Comment)
            type_ = "reply" if isComment else "PM"
            if message.author == AUTHOR:
                log.debug("Not forwarding {} by AUTHOR ({})".format(type_, AUTHOR))
                return

            log.info("Forwarding {} by {} to {}".format(type_, message.author, AUTHOR))

            reddit.redditor(AUTHOR).message(
                "Forwarding {} from u/{}".format(type_, message.author),
                (
                    "["
                    + message.body
                    + "]({})".format("https://reddit.com" + message.context)
                    if isComment
                    else message.body
                ),
            )
            message.mark_read()

        log.debug("Done. Checking spam-removed reports")
        for submission in reddit.subreddit("mod").mod.spam(only="submissions"):
            if submission.removed_by is None:
                log.info(f"approving spam-removed submission {submission}")
                submission.mod.approve()

        log.debug("..done")

    except RequestException as e:
        log.warning("Request exception while checking old reports: {}".format(str(e)))
    except ServerError as e:
        log.warning(
            "Server error while checking old reports: {}. Reddit likely under heavy load".format(
                str(e)
            )
        )
    except json.decoder.JSONDecodeError as e:
        log.warning(
            "JSONDecode exception while checking old reports: {}.".format(str(e))
        )
    except Exception as e:
        log.critical("some other error while checking reports: {}".format(str(e)))


def sweep():
    subreddit = reddit.subreddit(SUB)
    for submission in subreddit.new(limit=100):
        if DB_MAIN.submission_exists(submission.id):
            continue
        process_submission(submission, not args.comment, True)


if __name__ == "__main__":
    main()
