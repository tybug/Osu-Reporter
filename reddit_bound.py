class RedditBound:
    def __init__(self, submission, shouldComment, shouldFlair):
        '''
        Interface for objects that are tied to a specific reddit submission
        '''
        self.submission = submission
        self.title = submission.title.lower()
        self.post_id = submission.id
        self.short_link = "https://redd.it/" + self.post_id
        self.long_link = submission.permalink
        
        self.shouldComment = shouldComment
        self.shouldFlair = shouldFlair