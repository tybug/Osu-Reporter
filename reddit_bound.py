class RedditBound:
    """
    Interface for objects that are tied to a specific reddit submission.
    """

    def __init__(self, submission, shouldComment, shouldFlair):
        """
        Initializes a RedditBound instance.

        Submission submission: The reddit submission.
        Boolean shouldComment: Whether comments should be left on the submission.
        Boolean shouldFlair: Whether the flair of the submission should be modified.
        """

        self.submission = submission
        self.title = submission.title.lower()
        self.post_id = submission.id
        self.short_link = "https://redd.it/" + self.post_id
        self.long_link = submission.permalink
        self.text = submission.selftext

        self.shouldComment = shouldComment
        self.shouldFlair = shouldFlair
