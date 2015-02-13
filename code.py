import os
import webapp2
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import db


def renderTemplate(handler, templatename, templatevalues):
    path = os.path.join(os.path.dirname(__file__), 'templates/' + templatename)
    html = template.render(path, templatevalues)
    handler.response.out.write(html)


class MainPage(webapp2.RequestHandler):
    def get(self):
        user=users.get_current_user()
        global around
        global about
        global add
        title_link = ''
        title = ''
        type = ''
        message = ''
        log = ''
        if user:
            self.redirect('/search')

        else:
            type=(users.create_login_url('/search'))
            title_link=type
            message= ("Click to login")
            title="Login"
            log='Please Login'

        renderTemplate(self,'static-login-page.html', {
            "link": type,
            "message": message,
            "around": around,
            "add": add,
            "title": title,
            "log": log,
            "title_link": title_link,
            "about": about
        })
    #self.response.out.write("<html><body>%s</body></html>" % greeting)


class SearchPage(webapp2.RequestHandler):
    def get(self) :
        global about
        global around
        global add
        title_link=('/account')
        user=users.get_current_user()
        log=user.nickname()       
        renderTemplate(self,'static-search-page.html', {
            "title_link": '/account',
            "around": around,
            "message": log,
            "about": about,
            "add": add
        })


class DetailsPage(webapp2.RequestHandler):
    def get(self):
        global about
        global around
        global add
        title_link=(users.create_logout_url('/'))
        user=users.get_current_user()
        if user:
            log=user.nickname()
        else:
            log='Please login'
            self.redirect('/')
        renderTemplate(self,'static-information-page.html', {
            "name": 'test',
            "title_link": '/account',
            "around":around,
            "about":about,
            "add": add,
            "log": log
        })


class ProcessForm(webapp2.RequestHandler):
    def post(self):
        user=users.get_current_user()
        log=user.nickname()
        global around,about,add
        name = self.request.get('username')
        home = self.request.get('lat_long')
        renderTemplate(self, 'static-postupdate-page.html', {
            "log": log,
            "title_link": '/account',
            "about": about,
            "around": around,			
            "add": add			 
        })


class CreateLocation(webapp2.RequestHandler):
    def get(self):
        global about
        global around
        global add
        title_link=(users.create_logout_url('/'))
        user=users.get_current_user()
        if not user:
			self.redirect('/')
        name=user.nickname()
        renderTemplate(self,'static-location-creation-page.html', {
            "title_link": '/account',
            "around": around,
            "add": add,
            "log": name,
            "about": about
        })



class UpdateAccount(webapp2.RequestHandler):
    def get(self):
        global about
        global around
        global add		
        user=users.get_current_user()
        if not user:
			self.redirect('/')
        name=user.nickname()
        logout=users.create_logout_url('/')
        renderTemplate(self,'static-account-registration-page.html',{
        "account":'/account',
        "name": name,
        "logout": logout,
		"about": about,
		"around": around,
		"add": add
		})


class Account(db.Model):
    name = db.StringProperty(required=True)
    email = db.StringProperty(required=True)
    home = db.GeoPtProperty(required=True)

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/details', DetailsPage),
    ('/search', SearchPage),
    ('/update', ProcessForm),
    ('/account', UpdateAccount),
    ('/create', CreateLocation)
], debug=True)

around = '/search'
about = '/details'
add = '/create'