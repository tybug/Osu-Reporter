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

    users = {}
    c = sqlite3.connect("db.db")
    current_date = datetime.today()
    past_date = current_date - relativedelta.relativedelta(months=1)
    current_date = current_date.strftime("%m/%d/%Y")
    past_date = past_date.strftime("%m/%d/%Y")

    total_reports = c.execute("SELECT COUNT(*) FROM STATS").fetchone()[0] # .fetchone returns a tuple; get the first entry (number of rows)

    query = ("SELECT REPORTEE, "
             "COUNT(*) as num, "
             "SUM(CASE WHEN BLATANT = 'true' THEN 1 ELSE 0 END) AS BlatantCount "
             "FROM STATS "
             "GROUP BY REPORTEE "
             "ORDER BY num DESC "
             "LIMIT 5")
    for row in c.execute(query):
        users[row[0]] = [row[1], row[2]]

    query = ("SELECT COUNT(*) AS reports, "
            "SUM(CASE WHEN BLATANT = 'true' THEN 1 ELSE 0 END) AS blatant, "
            "SUM(CASE WHEN BLATANT = 'false' THEN 1 ELSE 0 END) AS normal, "
            "SUM(CASE WHEN RESTRICTED_UTC <> 'n/a' THEN 1 ELSE 0 END) AS restrictions, "
            "SUM(CASE WHEN BLATANT = 'true' AND RESTRICTED_UTC <> 'n/a' THEN 1 ELSE 0 END) AS 'blatant restrictions', "
            "SUM(CASE WHEN BLATANT = 'false' AND RESTRICTED_UTC <> 'n/a' THEN 1 ELSE 0 END) AS 'normal restrictions' "
            "FROM STATS")

    body = ("{} {} to {}.\n\nIn the past month, there were {} reports."
            "The 5 users with the most threads were:").format(rand.choice(intros), past_date, current_date, total_reports)
    
    print(body)
    print(",".join(users))
    