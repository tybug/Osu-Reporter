import sqlite3
from config import DB
from datetime import datetime
from dateutil import relativedelta
import random as rand

intros = ["Another month, another round of reports here on r/osureport. Here's your statistics for this month, from",
         "We're back with your monthly statistics report. Enjoy the sweet taste of data, from",
         "Gather 'round all, with the end of the month comes its stats. This set covers from",
         "You know the drill, statistics here for the 10 people that actually care. Covering from",
         "Not much to say, just here to drop off the latest set of statistics, fresh off the sql query. Extending from",
         "How ya doing today? I'm doing fine myself, thanks for asking. No one ever stops to consider how bots feel you know? Anyway, here's this month's statistics, from"]

def main():
    """
    Creates a statistics report from the db.db database
    """

    c = sqlite3.connect("db.db")
    current_date = datetime.today()
    past_date = current_date - relativedelta.relativedelta(months=1)
    current_date = current_date.strftime("%m/%d/%Y")
    past_date = past_date.strftime("%m/%d/%Y")


    stats = [] # [total reports, blatant reports, normal reports, total restrictions, blatant restrictions, normal restrictions]
    users = {}  # {"user": [total reports, blatant reports, reported users that got restricted], ...}
    average_time = 0

    query = ("SELECT COUNT(*) AS reports, "
            "SUM(CASE WHEN BLATANT = 'true' THEN 1 ELSE 0 END) AS blatant, "
            "SUM(CASE WHEN BLATANT = 'false' THEN 1 ELSE 0 END) AS normal, "
            "SUM(CASE WHEN RESTRICTED_UTC <> 'n/a' THEN 1 ELSE 0 END) AS restrictions, "
            "SUM(CASE WHEN BLATANT = 'true' AND RESTRICTED_UTC <> 'n/a' THEN 1 ELSE 0 END) AS 'blatantRestrictions', "
            "SUM(CASE WHEN BLATANT = 'false' AND RESTRICTED_UTC <> 'n/a' THEN 1 ELSE 0 END) AS 'normalRestrictions' "
            "FROM STATS")
    for row in c.execute(query):
        stats = [row[0], row[1], row[2], row[3], row[4], row[5]]


    query = ("SELECT REPORTEE, "
             "COUNT(*) as num, "
             "SUM(CASE WHEN BLATANT = 'true' THEN 1 ELSE 0 END) AS blatantCount, "
             "SUM(CASE WHEN RESTRICTED_UTC <> 'n/a' THEN 1 ELSE 0 END) AS restrictedCount "
             "FROM STATS "
             "GROUP BY REPORTEE "
             "ORDER BY num DESC "
             "LIMIT 5")
    for row in c.execute(query):
        users[row[0]] = [row[1], row[2], row[3]]


    query = ("SELECT AVG(DIFFERENCE) AS AVG FROM ( "
	                "SELECT "
	                "(RESTRICTED_UTC - REPORTED_UTC) AS DIFFERENCE "
	                "FROM STATS "
	        "WHERE RESTRICTED_UTC <> 'n/a')")

    average_restriction_seconds = c.execute(query).fetchone()[0]
    hours = average_restriction_seconds / 60 / 60

    body = ("{} {} to {}.\n\n"
            "# All Posts"
            "\n\n"
            "| Total Reports | Total Restrictions | Restriction Rate |\n"
            ":-:|:-:|:-:\n"
            "| {:,} | {:,} | {:.1f}% |"
            "\n\n"
            "| Normal Reports | Normal Restrictions | Normal Restriction Rate |\n"
            ":-:|:-:|:-:\n"
            "| {:,} | {:,} | {:.1f}% |"
            "\n\n"
            "| Blatant Reports | Blatant Restrictions | Blatant Restriction Rate |\n"
            ":-:|:-:|:-:\n"
            "| {:,} | {:,} | {:.1f}% |\n\n"
            "# Top 5 users by report count"
            "\n\n"
            "| User | Total Reports | Blatant Reports | Total reported users that got restricted | Total Restriction Rate |\n"
            ":-:|:-:|:-:|:-:|:-:\n"
            ).format(rand.choice(intros), past_date, current_date,
                    int(stats[0]), int(stats[3]), int(stats[3]) / int(stats[0]) * 100, # all
                    int(stats[2]), int(stats[5]), int(stats[5]) / int(stats[2]) * 100, # normal
                    int(stats[1]), int(stats[4]), int(stats[4]) / int(stats[1]) * 100) # blatant
    
    for user in users:
        data = users[user]
        body += ("| u/{} | {:,} | {:,} | {:,} | {:.1f}% |\n").format(user, int(data[0]), int(data[1]), int(data[2]), int(data[2]) / int(data[0]) * 100)

    body += ("\n# Average Restriction Time"
            "\n\n"
            "| Time |\n"
            ":-:\n"
            "{:.1f} hours").format(hours)


    print(body)    