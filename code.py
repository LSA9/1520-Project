import os
import webapp2
import datetime
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.api import search
from google.appengine.api import mail
from google.appengine.api import memcache
import json
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
        index = search.Index(name = "LocationIndex")

        results = index.search("name = " + self.request.get('search-value') + " OR address = " + self.request.get('search-value'))
        res = ""
        markers=[]
        if results:
            i = 0
            res += "<ul style='text-align: left; text-decoration: none; padding-top: 0; margin-top: 0;'>"
            for r in results:
                lat = ""
                s = r.field('locationInfo').value.find('(')
                e = r.field('locationInfo').value.find(',', s)
                lat = round(float(r.field('locationInfo').value[s+1:e]), 6)
                s = r.field('locationInfo').value.find(',')
                e = r.field('locationInfo').value.find(')', s)
                lng = round(float(r.field('locationInfo').value[s+1:e]), 6)
                markers.append({'lat': str(lat), 'lng': str(lng), 'title': r.field('name').value})
                res += "<br /><hr style='float: left; padding: 0px; margin: 0px;' /><a class='result' value='" + str(r.field('locationInfo').value) + "' href='/details/" + str(lat) + "/" + str(lng) + "' style='text-decoration: none; width: auto;'><li style='list-style: none; font-size:10pt; text-decoration: none; padding: 3px; margin-left: 4px;'>" + r.field('name').value + "</li></a>"
                if i > 10:
                    break
                i+=1
            res += "</ul>"
            res += '<a style="padding-top: 10px; margin-top:10px; text-decoration: none; font-size:12pt; color:#777777;" href="' + add + '"> + Create New Location </a>'
        data = json.dumps({'html': res, 'markers': markers})
        self.response.out.write(data)

    def tokenize_autocomplete(self, phrase):
        a = []
        for word in phrase.split():
            j = 1
        while True:
            for i in range(len(word) - j + 1):
                a.append(word[i:i + j])
                if j == len(word):
                    break
                j += 1
        return a


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
        favs = []
        for f in p.favorite:
            query = Location.query(Location.locationInfo == f)
            location = query.fetch()
            favs.append(location[0])
        log=p.name
        coord=p.home		
        renderTemplate(self,'static-search-page.html', {
            "title_link": '/account',
            "around": around,
            "message": log,
            "about": about,
            "add": add,
            "coord": coord,
            "favorites": favs
        })


class DetailsPage(webapp2.RequestHandler):
    @ndb.toplevel
    def get(self, lat, lng):
        global about
        global around
        global add
        user=users.get_current_user()
        if user:
            mail=user.email()
        else:
            self.redirect('/')
        q=ndb.gql("SELECT * FROM Account WHERE email = :1",mail)
        p=q.get()
        # lat = 40.442606
        # lng = -79.956686
        lat_long ='('+lat+', ' + lng+')';
        query = Location.query(Location.locationInfo == lat_long)
        location = query.fetch()
        if not location and len(location) == 0:
            self.redirect(add)
        val = 0
        hLatBound = float(lat) + .10
        lLatBound = float(lat) - .10
        hLngBound = float(lng) + .10
        lLngBound = float(lng) - .10
        qry1 = Location.query()
        qry2 = qry1.filter(Location.latitude > lLatBound)
        qry3 = qry2.filter(Location.latitude < hLatBound)
        locality = qry3.fetch()
        l = []
        for k in locality:
            if lLngBound < k.longitude and k.longitude < hLngBound and k.locationInfo != lat_long:
                l.append(k)
 #       for bv in location[0].businessValues:
        val += location[0].businessValues.value
        comments = location[0].messageList


        favs = ["(40.442606, -79.956686)"]
        if p.favorite:
            favs = p.favorite
        renderTemplate(self,'static-information-page.html', {
            "location_name": location[0].name,
            "location_latlng": lat_long,
            "location_lat": lat,
            "location_lng": lng,
            "title_link": '/account',
            "around": around,
            "about": about,
            "add": add,
            "log": p.name,
            "businessValue": val,
            "locality": l,
            "messageList": comments,
            "favorites": p.favorite
        })


class PostComment(webapp2.RequestHandler):
    def post(self, lat, lng):
        lat_long ='('+lat+', ' + lng+')'
        query = Location.query(Location.locationInfo == lat_long)
        location = query.fetch()
        user=users.get_current_user()
        mail=user.email()
        q=ndb.gql("SELECT * FROM Account WHERE email = :1",mail)
        p=q.get()
        mp = MessagePost(user=p.name, time="12:27 pm 3/16/2015", message=self.request.get("msg"))
        location[0].messageList.append(mp)
        location[0].put()
        self.redirect("/details/"+lat+"/"+lng)

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
        coord=nhome
        log=nname
        if not p:
            u=Account(email=user.email(), name=nname, home=nhome, favorite=[])
            u.put()
        else:
            p.name=nname
            p.home=nhome
            p.put()

        renderTemplate(self,'static-search-page.html', {
            "title_link": '/account',
            "around": around,
            "message": log,
            "about": about,
            "add": add,
            "coord": coord,
        })


class CreateLocation(webapp2.RequestHandler):
    def get(self):
        global about
        global around
        global add
        user=users.get_current_user()
        if not user:
            self.redirect('/')
        mail = user.email()
        q=ndb.gql("SELECT * FROM Account WHERE email = :1",mail)
        p = q.get()
        name=p.name
        title_link=('/account')
        renderTemplate(self,'static-location-creation-page.html', {
            "title_link": '/account',
            "around": around,
            "add": add,
            "log": name,
            "about": about
        })
    @ndb.toplevel
    def post(self):
        global around
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

            loc = Location(latitude=lat, longitude=lng, locationInfo=lat_long, name=self.request.get('location_name'), messageList=[], businessValues=bv)
            loc.put()
        my_document = search.Document(
            # Setting the doc_id is optional. If omitted, the search service will create an identifier.
            fields=[
                search.TextField(name='locationInfo',value = lat_long),
                search.TextField(name='name', value = self.request.get('location_name')),
                search.TextField(name='address', value= self.request.get('address'))
            ])
        try:
            index = search.Index(name="LocationIndex")
            index.put(my_document)
        except search.Error:
            print("ERROR")

        i = 0
        query = Location.query(Location.locationInfo == lat_long)
        location = query.fetch()
        while not location:
            query = Location.query(Location.locationInfo == lat_long)
            location = query.fetch()
            if i > 100000:
                self.redirect(around)
            i+=1

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

        name = user.nickname()
        logout=users.create_logout_url('/')
        renderTemplate(self,'static-account-registration-page.html',{
            "account": '/account',
            "name": nickname,
            "nickname":nickname,
            "local": local,
            "logout": logout,
            "about": about,
            "around": around,
            "add": add,
            "ll":latlong,
        })

class AboutUs(webapp2.RequestHandler):
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
        else:
            nickname=p.name
        name = user.nickname()
        logout=users.create_logout_url('/')
        renderTemplate(self,'about-page.html', {
            "account": '/account',
            "name": nickname,
            "nickname": nickname,
            "logout": logout,
            "about": about,
            "around": around,
            "add": add,
        })

class AsyncFavoriteAdd(webapp2.RequestHandler):
    def post(self):
        global about
        global around
        global add
        user=users.get_current_user()
        mail=user.email()
        if not user:
            self.redirect('/')
        q=ndb.gql("SELECT * FROM Account WHERE email = :1",mail)
        p=q.get()
        if p:
            p.favorite.append("(" + self.request.get("lat") + ", " + self.request.get("lng") + ")")
            p.put()




class ContactUs(webapp2.RedirectHandler):
    def get(self):
        self.redirect('/about')

    def post(self):
        user_addr = self.request.get('email')
        email = ""
        if not mail.is_email_valid(user_addr):
            email += "No valid return address.\n"
        else:
            email += "Return Address: " + user_addr + "\n"
        email += "Name: " + self.request.get('name') + "\n"
        email += "Comment: " + self.request.get('content')
        print(email)
        mail.send_mail("gaggle1520@gmail.com", "gaggle1520@gmail.com", "Comment from "+self.request.get('name'), email)
        self.redirect('/about')


class Account(ndb.Model):
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True)
    home = ndb.StringProperty(required=True)
    favorite=ndb.StringProperty(repeated=True)	


class BusinessValue(ndb.Model):
    value = ndb.IntegerProperty(required=True)
    comment = ndb.StringProperty()
    user = ndb.UserProperty()

class MessagePost(ndb.Model):
    message = ndb.StringProperty(required=True)
    user = ndb.StringProperty(required=True)
    time = ndb.StringProperty(required=True)

class Location(ndb.Model):
    latitude = ndb.FloatProperty(required=True)
    longitude = ndb.FloatProperty(required=True)
    locationInfo = ndb.StringProperty(required=True)
    name = ndb.StringProperty(required=True)
    businessValues = ndb.StructuredProperty(BusinessValue,required=True)
    messageList = ndb.StructuredProperty(MessagePost, repeated=True)



app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/comment/details/([^/]+)/([^/]+)', PostComment),
    ('/details/([^/]+)/([^/]+)', DetailsPage),
    ('/search/async', AsyncSearch),
    ('/search', SearchPage),
    ('/update', ProcessForm),
    ('/account', UpdateAccount),
    ('/create', CreateLocation),
    ('/about/contact', ContactUs),
    ('/about', AboutUs),
    ('/favorite', AsyncFavoriteAdd)
], debug=True)

dummy='test'
around = '/search'
about = '/about'
add = '/create'