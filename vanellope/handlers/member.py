#! /usr/bin/env python
# coding=utf-8

import re
import hashlib
import urllib
import urlparse
import datetime
import smtplib
import string
import random
import json
import config

import tornado.web

from vanellope import da
from vanellope import db

from vanellope import Mail
from vanellope import regex
from vanellope import constant as cst

from vanellope.model import Member
from vanellope.model import Article
from vanellope.handlers import BaseHandler


class MemberHandler(BaseHandler):
    # UTL: /member/USERNAME
    # Member main information display
    #
    def get(self, uid):
        m = Member(self.get_current_user())
        page = self.get_argument("p", 1)
        author = Member(da.get_member_by_uid(uid))

        d = da.split_pages(author=author.uid, page=page)

        if author.uid is None:
            self.send_error(404)
            self.finish()
        elif m.uid == author.uid:
            self.redirect("/home")
        else:
            member = dict(
                avatar_large = author.avatar_large,
                brief = author.brief,
                name = author.name
            )

        master = dict(
            color = m.color,
            name = m.name,
        )

        self.render("member.html",
                    title = member['name'],
                    articles = d['articles'],
                    member = member,
                    pages = d['pages'],
                    master = master) 

class HomeHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, html="home"):
        m = Member(self.get_current_user())
        master = dict(
            uid = m.uid,
            color = m.color,            
            avatar_large = m.avatar_large,
            brief = m.brief,
            name = m.name,
            email = m.email,
        )

        htmls = ('write', 'index', 'deleted')

        template = ("%s.html" % html)
        #page = self.get_argument("p", 1)
        
        if(html == "deleted"):
            #d = da.split_pages(author=master['uid'], page=page, status=cst.DELETED)
            #articles = da.deleted_or_normal_articles(master['uid'], cst.NOTMAL)
            self.render(template, 
                        title = '回收站', 
                        master = master,
                        errors=None,                        
                        #articles = d['artices']
                        )
        else:
            #d = da.split_pages(author=master['uid'], page=page, status=cst.NORMAL)
            #articles = da.deleted_or_normal_articles(master['uid'], cst.DELETED)
            self.render(template, 
                        title="Home",
                        errors=None,                        
                        master = master,
                        #pages = d['pages'],
                        #articles = d['articles']
                        )

    @tornado.web.authenticated
    def post(self):
        master = self.get_current_user()
        if master:
            brief = self.get_argument('brief', default=None)
            db.member.update({"uid":master['uid']},{"$set":{"brief":brief}})
            member = db.member.find_one({'uid': master['uid']})
            self.finish(brief)
        else:
            self.send_error(403)
            self.findish()

    def get_author_all_articles(self, owner_id):
        return db.article.find({"author": owner_id}).sort("date", -1)

    def normal_articles(self, owner_id):
        return db.article.find(
                {"author": owner_id, "status":cst.NORMAL}).sort("date", -1)

    def deleted_articles(self, owner_id):
        return db.article.find(
                {"author": owner_id, "status":"deleted"}).sort("date", -1)

    def count_pages(self, owner_id=None, p=10, status="normal"):
        # p, articles per page
        p = int(p)
        if owner_id: # one member's
            total = db.article.find(
                {"status":status, "author":owner_id}).count()
        else: # all members'
            total = db.article.find({"status":status}).count()
        pages = total // p + 1 # pages count from 1
        if total % p > 0:      # the last page articles may not equal to 'p' 
            pages += 1 
        return pages
  
  
                      
class EmailHandler(BaseHandler):
    # ajax call
    @tornado.web.authenticated
    def get(self):
        master = self.get_current_user()
        self.write(master['email'])
        self.flush()
        self.finish()

    # ajax call
    # BUG: even if email not verified still can go.
    def post(self):
        errors = []
        _email = self.get_argument("email", None)
        if re.match(regex.EMAIL, _email):
            ex = db.member.find_one({"email":_email})
            if not ex:
                master = self.get_current_user()
                master['email'] = _email.lower()
                db.member.save(master)
            else:
                errors.append(u"邮箱已被使用")
        else:
            errors.append(u"请检查邮箱的格式是否正确")
        if len(errors) > 0:
            self.write(json.dumps(errors))
        else:
            self.write(json.dumps(True))
        self.flush()
        self.finish()