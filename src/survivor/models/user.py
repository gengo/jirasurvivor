from urllib2 import quote

from mongoengine import *
from mongoengine.queryset import QuerySet

from survivor import config

class UserQuerySet(QuerySet):
    """
    Custom user queries.
    """
    def competitors(self):
        return filter(lambda u: u.leaderboard_user(), self.all())

    def developers(self):
        return self.competitors()

class User(Document):
    """
    A JIRA user.
    """
    meta = {'queryset_class': UserQuerySet}

    login = StringField(required=True, unique=True)
    name = StringField()
    email = StringField()
    avatar_url = StringField()

    def __init__(self, **kwargs):
        self._closed_issues = None
        Document.__init__(self, **kwargs)

    def assigned_issues(self):
        return self.issues('open')

    def closed_issues(self):
        from survivor.models.issue import Issue
        return Issue.objects(assignee=self, state="closed", finished_or_fixed=True)

    def reported_issues(self):
        from survivor.models.issue import Issue
        return Issue.objects(reporter=self)

    def issues(self, state):
        from survivor.models.issue import Issue
        return Issue.objects(assignee=self, state=state)

    def leaderboard_user(self):
        "Returns true if user should be included in leaderboards."
        whitelist = config['leaderboard_users']
        return not whitelist or self.login in whitelist

    def assigned_issues_url(self):
        return '%s/issues/?jql=' % config['jira.server'] + \
            quote('project = %s AND status = Open AND assignee = "%s"' % (config['jira.project'],
                                                                          self.login))
