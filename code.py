import os
import webapp2
import unicodedata
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import ndb


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
        
        #p=q.get()
    
		
        if user:
            mail=user.email()
            q=ndb.gql("SELECT * FROM Account WHERE email = :1",mail)
            p=q.get()			
            if not p:               
                self.redirect('/account')			
            else:
			    self.redirect('/search')

        else:
            type=(users.create_login_url('/'))
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
        user=users.get_current_user()
        mail=user.email()
        q=ndb.gql("SELECT * FROM Account WHERE email = :1",mail)
        p=q.get()
        title_link=('/account')
        
        log=p.name
        coord=p.home		
        renderTemplate(self,'static-search-page.html', {
            "title_link": '/account',
            "around": around,
            "message": log,
            "about": about,
            "add": add,
            "coord": coord
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
        lat = 40.442606
        lng = -79.956686
        query = Location.query()
        query.filter(locationInfo = (40.442606, -79.956686))
        location = query.fetch()
        val = 0
        for BusinessValue in location:
            val += BusinessValue.value

        renderTemplate(self,'static-information-page.html', {
            "name": 'test',
            "title_link": '/account',
            "around":around,
            "about":about,
            "add": add,
            "log": log,
            "businessValue" : val
        })


class ProcessForm(webapp2.RequestHandler):
    def post(self):
        user=users.get_current_user()
        log=user.nickname()
        mail=user.email()
        global around,about,add
        nname = self.request.get('username')
        nhome = self.request.get('lat_long')
        q=ndb.gql("SELECT * FROM Account WHERE email = :1",mail)
        p=q.get()
        if not p:
            u=Account(email=user.email(), name=nname, home=nhome)
            u.put()
        else:
            p.name=nname 
            p.home=nhome
            p.put()
            			
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
        mail=user.email()
        if not user:
		    self.redirect('/')
        q=ndb.gql("SELECT * FROM Account WHERE email = :1",mail)
        p=q.get()	
        if not p:
            nickname=''
            local=''
            latlong="(40.442606, -79.956686)"			
        else:
            nickname=p.name
            local=p.home
            latlong=local			
        name=user.nickname()
        logout=users.create_logout_url('/')
        renderTemplate(self,'static-account-registration-page.html',{
        "account":'/account',
        "name": name,
        "nickname":nickname,
        "local": local,		
        "logout": logout,
		"about": about,
		"around": around,
		"add": add,
		"ll":latlong
		})


class Account(ndb.Model):
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True)
    home = ndb.StringProperty(required=True)

class BusinessValue(ndb.Model):
    value = ndb.IntegerProperty(required=True)
    comment = ndb.StringProperty()
    user = ndb.UserProperty()	
	
class Location(ndb.Model):
    locationInfo = ndb.GeoPtProperty(required=True)
    name = ndb.StringProperty(required=True)
    businessValues = ndb.StructuredProperty(BusinessValue,required=True)




app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/details', DetailsPage),
    ('/search', SearchPage),
    ('/update', ProcessForm),
    ('/account', UpdateAccount),
    ('/create', CreateLocation)
], debug=True)

dummy='test'
around = '/search'
about = '/details'
add = '/create'