import os
import webapp2
import unicodedata
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import ndb
from google.appengine.ext import search
import re

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

class AsyncSearch(webapp2.RequestHandler):
    def get(self):
        print(self.request.get('search-value')+" a--------------------------------------")
        query = Location.query(Location.name == self.request.get('search-value'))
        locs = query.fetch()
        res = ""
        res += "<ul style='text-align: left; width:100%'>"
        for loc in locs:
            lat = ""
            s = loc.locationInfo.find('(')
            e = loc.locationInfo.find(',', s)
            lat = round(float(loc.locationInfo[s+1:e]), 6)
            s = loc.locationInfo.find(',')
            e = loc.locationInfo.find(')', s)
            lng = round(float(loc.locationInfo[s+1:e]), 6)
            res += "<hr style='float: left;'  /><br /><a href='/details/" + str(lat) + "/" + str(lng) + "'><li style='list-style: none; font-size:18pt; text-decoration: none;'>" + loc.name + "</li></a>"
        res += "</ul>"
        self.response.out.write(res)


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
    def get(self, lat, lng):
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
        # lat = 40.442606
        # lng = -79.956686
        lat_long ='('+lat+', ' + lng+')';
        query = Location.query(Location.locationInfo == lat_long)
        location = query.fetch()
        if not location:
            self.redirect(add)
        val = 0
 #       for bv in location[0].businessValues:
        val += location[0].businessValues.value

        renderTemplate(self,'static-information-page.html', {
            "location_name": location[0].name,
            "location_latlng": lat_long,
            "title_link": '/account',
            "around": around,
            "about": about,
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

    def post(self):
        lat = ""
        s = self.request.get('lat_long').find('(')
        e = self.request.get('lat_long').find(',', s)
        lat = round(float(self.request.get('lat_long')[s+1:e]), 6)
        s = self.request.get('lat_long').find(',')
        e = self.request.get('lat_long').find(')', s)
        lng = round(float(self.request.get('lat_long')[s+1:e]), 6)
        lat_long = '(' + str(lat) + ', ' + str(lng) + ')'
        query = Location.query(Location.locationInfo == lat_long)
        location = query.fetch()
        if location:
            self.redirect('/details/'+str(lat)+'/'+str(lng))
        else:
            bv = BusinessValue(value=5)

            loc = Location(locationInfo=lat_long, name=self.request.get('location_name'), businessValues=bv)
            loc.put()
        print(lat_long +"   u0u{")
        self.redirect('/details/'+str(lat)+'/'+str(lng))


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
    locationInfo = ndb.StringProperty(required=True)
    name = ndb.StringProperty(required=True)
    businessValues = ndb.StructuredProperty(BusinessValue,required=True)



app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/details/([^/]+)/([^/]+)', DetailsPage),
    ('/search/async', AsyncSearch),
    ('/search', SearchPage),
    ('/update', ProcessForm),
    ('/account', UpdateAccount),
    ('/create', CreateLocation)
], debug=True)

dummy='test'
around = '/search'
about = '/details/40.442573/-79.956675'
add = '/create'