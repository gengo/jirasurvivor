"""
Synchronises local database with JIRA.
"""

import argparse
import itertools

from jira.client import JIRA

from survivor import config, init
from survivor.models import User, Issue

# max number of issues to have jira return for the project
MAX_ISSUE_RESULTS = 99999

def create_user(jira_user):
    "Creates a `survivor.models.User` from a `jira.resources.User`."
    user = User(login=jira_user.name)
    user.name = jira_user.displayName
    user.email = jira_user.emailAddress
    user.avatar_url = jira_user.avatarUrls.__dict__['48x48']

    return user.save()

def get_or_create_user(jira_user):
    """
    Get or create a `survivor.models.User` from a partially-loaded
    `jira.resources.User`.
    """
    try:
        return User.objects.get(login=jira_user.name)
    except User.DoesNotExist:
        return create_user(jira_user)

# Map primitive survivor.models.Issue attrs to jira.resources.Issue attrs
issue_attr_map = {
    'key': 'key',
    'title': 'title',
    'state': 'fields.status.name',
    'opened': 'created',
    'closed': 'resolutiondate',
    'updated': 'updated',
    'url': 'self',
    }

def create_issue(jira_issue):
    "Creates a `survivor.models.Issue` from a `jira.resources.Issue`."
    issue = Issue(**dict((issue_attr, getattr(jira_issue, jira_attr))
                         for issue_attr, jira_attr in issue_attr_map.items()))

    issue.reporter = get_or_create_user(jira_issue.fields.reporter)
    if jira_issue.assignee:
        issue.assignee = get_or_create_user(jira_issue.fields.assignee)

    # TODO comments, labels

    return issue.save()

def sync(types, verbose=False):
    "Refresh selected collections from JIRA."

    jira_project = config['jira.project']
    jira_username = config['jira.username']
    jira_password = config['jira.password']
    jira_server = config['jira.server']

    jira = JIRA(basic_auth=(jira_username, jira_password), options={'server': jira_server})

    if 'users' in types:
        User.drop_collection()
        # FIXME: can this come from config?
        for jira_user in jira.jira.search_assignable_users_for_projects('shawn.smith', 'GEN'):
            try:
                user = create_user(jira_user)
            except:
                print 'Error creating user: %s' % jira_user.name
                raise
            if verbose: print 'created user: %s' % jira_user.name

    if 'issues' in types:
        Issue.drop_collection()
        """
        issues = itertools.chain(repo.get_issues(state='open'),
                                 repo.get_issues(state='closed'))
        """
        issues = issues_in_proj(
            jira.search_issues('project=%s and (status=OPEN or status=CLOSED)' % jira_project,
                maxResults=MAX_ISSUE_RESULTS)
        )
        for jira_issue in issues:
            try:
                issue = create_issue(jira_issue)
            except:
                print 'Error creating %s' % jira_issue.key
                raise
            if verbose: print 'created issue: %s' % jira_issue.key

if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description='Synchronises local DB with JIRA')
    argparser.add_argument('model', nargs='*', help='model types to sync')
    argparser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='verbose output')

    args = argparser.parse_args()
    types = args.model or ('users', 'issues')

    init()
    sync(types, args.verbose)
