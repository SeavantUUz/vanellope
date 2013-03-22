# /usr/bin/env python
# coding=utf-8

import datetime

import tornado.web
from markdown import markdown
from vanellope.ext import db
from vanellope.model import Article
from vanellope.handlers import BaseHandler

class ArticleHandler(BaseHandler):
    def get(self, sn):
        article = db.article.find_one({"status": "normal", 'sn': int(sn)})
        if not article:
            self.send_error(404)
            self.finish()

        author = db.member.find_one({'uid': article['author'] })
        cursor = db.comment.find({'article': int(sn)}).sort('date',1)
        comments = []
        for comment in cursor:
            comment['date'] += datetime.timedelta(hours=8)
            comment['date'] = comment['date'].strftime("%Y-%m-%d %H:%M")
            comments.append(comment)

        article['heat'] += 1
        db.article.save(article)

        adjoins = self.find_adjoins(article['date'])

        article['body'] = article['html']
        article['brief'] = article['sub_title']
        article['date'] += datetime.timedelta(hours=8)
        article['date'] = article['date'].strftime("%Y-%m-%d %H:%M")
        article['review'] += datetime.timedelta(hours=8)
        article['review'] = article['review'].strftime("%Y-%m-%d %H:%M")

        self.render("article.html", 
                    pre = adjoins[0],
                    fol = adjoins[1],
                    master = self.get_current_user(),
                    comments = comments, 
                    title = article['title'],
                    author = author, 
                    article = article)

    #create article
    @tornado.web.authenticated
    def post(self):
        model = {
            'sn': None, # article numeric id
            'status': "normal", # 'deleted', 'normal',
            'author': None, #
            'heat': 0,
            'title': None,
            'sub_title': None,
            'markdown': None,
            'html': None,
            'date': datetime.datetime.utcnow(),
            'review': datetime.datetime.utcnow(),
            'permalink': None,
            'category': None,
        }

        # get post values
        post_values = ['intro-img', 'title', 'brief', 'content']
        args = {}
        for v in post_values:
            try:
                args[v] = self.get_argument(v)
            except:
                pass
        if db.article.count() == 0:
            model['sn'] = 0;
        else:
            model['sn'] = db.article.find().sort("sn", -1)[0]['sn'] + 1
        model['status'] = 'normal'
        model['title'] = args['title']
        model['sub_title'] = args['brief']
        model['markdown'] = args['content']
        model['html'] = markdown(args['content'], ['fenced_code', 'codehilite'], safe_mode= "escape")

        try:     
            master = self.get_current_user()
            model['author'] = master['uid']
            db.article.insert(model)
            self.redirect('/')
        except:
            logging.warning("Unexpecting Error")

    @tornado.web.authenticated
    def delete(self, article_sn):
        article = db.article.find_one({"sn": int(article_sn)})
        article['status'] = "deleted"
        db.article.save(article)
        self.set_status(200)
        self.finish()

    def find_adjoins(self, current_date):
        try:
            pre = db.article.find({'date':
                {'$lt': current_date}}).sort("date",-1)[0]['sn']
        except:
            pre = None
        try:
            fol = db.article.find({'date': 
                {"$gt": current_date}}).sort("date", 1)[0]['sn']
        except:
            fol = None
        return (pre, fol)
        

class ArticleUpdateHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, sn):
        article = db.article.find_one({'sn': int(sn)})
        author = db.member.find_one({'uid': article['author']})

        self.render("home/edit.html", 
                    master = self.get_current_user(),
                    title = "Edit",
                    author = author,
                    article = article)

    @tornado.web.authenticated
    def post(self, sn):
        post_values = ['title', 'brief', 'content']
        args = {}
        for v in post_values:
            try:
                args[v] = self.get_argument(v)
            except:
                continue

        master = self.get_current_user()
        article = db.article.find_one({"sn":int(sn)})
        
        if master:
            article['title']  = args['title']
            article['brief'] = args['brief']
            article['markdown'] = args['content']
            article['html'] = markdown(args['content'], ['fenced_code',  'codehilite'], safe_mode="escape" )
            article['review'] = datetime.datetime.utcnow()
            db.article.update({"sn":int(sn)}, article)
            self.redirect("/article/%s" % sn)
        else:
            self.send_error(403)    

class RecoverHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self, article_sn):
        # Ajax Call:
        # recover deleted article
        #
        article = db.article.find_one({"sn": int(article_sn)})
        article['status'] = "normal"
        db.article.save(article)
        self.set_status(200)
        return True
        