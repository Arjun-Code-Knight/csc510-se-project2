from __future__ import print_function
import urllib2
import json
import re,datetime
import sys
import pymongo
from pymongo import MongoClient

client =  MongoClient()
db = client['SE510']

issue_collection = db['Issue']
 
class L():
  "Anonymous container"
  def __init__(i,**fields) : 
    i.override(fields)
  def override(i,d): i.__dict__.update(d); return i
  def __repr__(i):
    d = i.__dict__
    name = i.__class__.__name__
    return name+'{'+' '.join([':%s %s' % (k,pretty(d[k])) 
                     for k in i.show()])+ '}'
  def show(i):
    lst = [str(k)+" : "+str(v) for k,v in i.__dict__.iteritems() if v != None]
    return ',\t'.join(map(str,lst))

  
def secs(d0):
  d     = datetime.datetime(*map(int, re.split('[^\d]', d0)[:-1]))
  epoch = datetime.datetime.utcfromtimestamp(0)
  delta = d - epoch
  return delta.total_seconds()

def dumpCommit1(u,commits,token):
  request = urllib2.Request(u, headers={"Authorization" : "token "+token})
  v = urllib2.urlopen(request).read()
  w = json.loads(v)
  if not w: return False
  
  for commit in w:
    #data=[]  
    sha = commit['sha']
    user = commit['author']['login']
    time = secs(commit['commit']['author']['date'])
    message = commit['commit']['message']
    commitObj = L(
                user = user,
                time = time,
                message = message)
    data = commits.get(sha)
    if not data: data = []
    data.append(commitObj)
    commits[sha]=data
  return True
  
def dumpComments1(u, comments, token):
  request = urllib2.Request(u, headers={"Authorization" : "token "+token})
  v = urllib2.urlopen(request).read()
  w = json.loads(v)
  if not w: return False
  #data=[]
  for comment in w:
    user = comment['user']['login']
    identifier = comment['id']
    issueid = int((comment['issue_url'].split('/'))[-1])
    comment_text = comment['body']
    created_at = secs(comment['created_at'])
    updated_at = secs(comment['updated_at'])
    commentObj = L(
                issue = issueid,
                user = user,
                text = comment_text,
                created_at = created_at,
                updated_at = updated_at)
    data = comments.get(identifier)
    if not data: data = []	
    data.append(commentObj)
    comments[identifier]=data	
  return True
  
def dumpMilestone1(u, milestones, token):
  request = urllib2.Request(u, headers={"Authorization" : "token "+token})
  v = urllib2.urlopen(request).read()
  w = json.loads(v)
  if not w or ('message' in w and w['message'] == "Not Found"): return False
  #data=[]
  milestone = w
  identifier = milestone['id']
  milestone_id = milestone['number']
  milestone_title = milestone['title']
  milestone_description = milestone['description']
  created_at = secs(milestone['created_at'])
  due_at_string = milestone['due_on']
  due_at = secs(due_at_string) if due_at_string != None else due_at_string
  closed_at_string = milestone['closed_at']
  closed_at = secs(closed_at_string) if closed_at_string != None else closed_at_string
  user = milestone['creator']['login']
  open_issues=milestone['open_issues']
  closed_issues=milestone['closed_issues']
  state=milestone['state']
  milestoneObj = L(
               m_id = milestone_id,
               m_title = milestone_title,
               m_description = milestone_description,
               created_at=created_at,
               due_at = due_at,
               closed_at = closed_at,
               user = user,
			   open_issues=open_issues,
			   closed_issues=closed_issues,
			   state=state)
  data = milestones.get(identifier)
  if not data: data = []  
  data.append(milestoneObj)
  milestones[identifier]=data
  return True

def dumpComments(u,comments, token):
  try:
    return dumpComments1(u,comments,token)
  except Exception as e: 
    print(u)
    print(e)
    return False
 
def dump1(u,issues):
  token = "xyz" # <===
  request = urllib2.Request(u, headers={"Authorization" : "token "+token})
  v = urllib2.urlopen(request).read()
  w = json.loads(v)
  if not w: return False
  for event in w:
    issue_id = event['issue']['number']
    action = event['event']
    #if not event.get('label'): continue
    label_name=None
    assignee=None
    assigner=None
    if 'label' in event:
        label_name = event['label']['name']
    elif action == 'assigned':
        assignee=event['assignee']['login']
        assigner=event['assigner']['login']		
    created_at = secs(event['created_at'])
    
    #label_name = event['label']['name']
    user = event['actor']['login']
    milestone = event['issue']['milestone']
    if event['issue']['closed_at']: 
        closed_at=secs(event['issue']['closed_at'])
    else:
        closed_at=event['issue']['closed_at']
    #assignee=event['issue']['assignee']['login']
    state=event['issue']['state']	
    if milestone != None : milestone = milestone['title']
    eventObj = L(when=created_at,
                 action = action,
                 what = label_name,
                 user = user,
                 milestone = milestone,
				 closed=closed_at,
				 assignee=assignee,
				 assigner=assigner,
				 state=state)
    all_events = issues.get(issue_id)
    if not all_events: all_events = []
    all_events.append(eventObj)
    issues[issue_id] = all_events
  return True

def dumpComments(u,comments, token):
  try:
    return dumpComments1(u,comments,token)
  except Exception as e: 
    print(u)
    print(e)
    return False

def dumpMilestone(u,milestones,token):
  try:
    return dumpMilestone1(u, milestones,token)
  except urllib2.HTTPError as e:
    if e.code != 404:
      print(e)
      print("404 Contact TA")
    return False
  except Exception as e:
    print(u)
    print(e)
    print("other Contact TA")
    return False

def dump(u,issues):
  try:
    return dump1(u, issues)
  except Exception as e: 
    print(e)
    print("Contact TA")
    return False

def dumpCommit(u,commits, token):
  try:
    return dumpCommit1(u,commits,token)
  except Exception as e: 
    print(u)
    print(e)
    return False
	
def launchDump():
  page = 1
  issues = dict()
  commits=dict()
  comments=dict()
  milestones=dict()
  token = "xyz"
  repo="Arjun-Code-Knight/csc510-se-project"
  group="A"
  
  while(True):
    doNext = dump('https://api.github.com/repos/'+repo+'/issues/events?page=' + str(page), issues)
    print("page "+ str(page))
    page += 1
    ##added
    
    if not doNext : break
  page=1
  
  while(True):
    url = 'https://api.github.com/repos/'+repo+'/commits?page=' + str(page)
	#'https://api.github.com/repos/'+repo+'/commits?page=' + str(page)
    doNext = dumpCommit(url, commits, token)
    print("commit page "+ str(page))
    page += 1
    if not doNext : break
  page=1
  
  while(True):
    url = 'https://api.github.com/repos/'+repo+'/issues/comments?page='+str(page)
	#'https://api.github.com/repos/'+repo+'/issues/comments?page='+str(page)
    doNext = dumpComments(url, comments, token)
    print("comments page "+ str(page))
    page += 1
    if not doNext : break
  page=1
  while(True):
    url = 'https://api.github.com/repos/'+repo+'/milestones/'+str(page)
	#'https://api.github.com/repos/'+repo+'/milestones/' + str(page)
    doNext = dumpMilestone(url, milestones, token)
    print("milestone "+ str(page))
    page += 1
    if not doNext : break
  '''
  for issue, events in issues.iteritems():
    print("ISSUE " + str(issue))
    for event in events: print(event.show())
    print('')
  '''
  client =  MongoClient()
  db = client['SE510']

  issue_collection = db['Issue']
  commits_collection = db['Commits']
  comments_collection = db['Comments']
  milestones_collection=db['Milestones']
  
  for commit,info in commits.iteritems():
	for data in info:
		commits_collection.insert({
			"id":commit,
			"user":data.user,
			"time":data.time,
			"message":data.message,
			"group":group
			})
			
  
  
  for comment,info in comments.iteritems():
	for data in info:
		comments_collection.insert({
			"id":comment,
			"issue":data.issue,
			"user":data.user,
			"text":data.text,
			"created":data.created_at,
			"updated":data.updated_at,
			"group":group
			})
  
  for id,info in milestones.iteritems():
	for data in info:
		milestones_collection.insert({
			"id":id,
			"number":data.m_id,
			"title":data.m_title,
			"description":data.m_description,
			"created":data.created_at,
			"due":data.due_at,
			"closed":data.closed_at,
			"user":data.user,
			"open_issues":data.open_issues,
			"closed_issues":data.closed_issues,
			"state":data.state,
			"group":group
			})
  
  for issue,events in issues.iteritems():
	for event in events:
		issue_collection.insert({
		  "issue_id" : issue,
		  "when" : event.when,
		  "action": event.action,
		  "what":event.what,
		  "user":event.user,
		  "milestone":event.milestone,
		  "closed":event.closed,
		  "assignee":event.assignee,
		  "assigner": event.assigner,
		  "state" :event.state,
		  "group":group
		  #"events" : issues.get(issue)
		})
  
launchDump()