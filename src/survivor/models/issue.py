from datetime import datetime

from mongoengine import *
from mongoengine.queryset import QuerySet

from survivor.models import User

class IssueQuerySet(QuerySet):
    """
    Custom issue queries.
    """
    def opened_in(self, start, end):
        "Find issues opened in date range."
        return self.filter(opened__gt=start, opened__lte=end)

    def older_than(self, date):
        "Find open issues created before a given date."
        return self.filter(opened__lt=date, state='open')

    def closed_in(self, start, end):
        "Find issues closed in date range."
        return self.filter(closed__gt=start, closed__lte=end)

    def open_at(self, time):
        "Find open issues at a point in time."
        return self.filter(opened__lt=time, closed__not__lt=time)

    def unassigned(self):
        "Find unassigned open issues."
        return self.filter(state='open', assignee=None)

class Issue(Document):
    """
    A JIRA Issue
    """
    meta = {'queryset_class': IssueQuerySet}

    key = StringField(unique=True, required=True)
    title = StringField()
    state = StringField()
    assignee = ReferenceField(User, dbref=False)
    reporter = ReferenceField(User, dbref=False)
    closed = DateTimeField()
    opened = DateTimeField(required=True)
    updated = DateTimeField(required=True)
    url = URLField()
