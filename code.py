import os
import webapp2
import datetime
import time
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.api import search
from google.appengine.api import mail
from google.appengine.api import memcache
import json
import logging
import re
import math
import string
import operator


os.environ['TZ'] = "US/Eastern"

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
                return
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
        index = search.Index(name = "LocationIndexDoc")

        results = index.search("name = " + self.request.get('search-value') + " OR address = " + self.request.get('search-value'))
        res = ""
        markers=[]
        nw = now_eastern(datetime.datetime.now()).hour
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
                lat_long ='('+str(lat)+', ' + str(lng) +')'
                query = Location.query(Location.locationInfo == lat_long)
                location = query.fetch()
                markers.append({'lat': str(lat), 'lng': str(lng), 'title': r.field('name').value, 'color' : str(rgbCalc(location[0].currentValue))})
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
        if not user:
            self.redirect('/')
            return
        mail=user.email()
        q=ndb.gql("SELECT * FROM Account WHERE email = :1",mail)
        p=q.get()
        if not p:
            self.redirect('/account')
            return
        title_link=('/account')
        favs = []
        for f in p.favorite:
            query = Location.query(Location.locationInfo == f)
            location = query.fetch()
            if len(location) != 0 and location:
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


digs = string.digits + string.letters
def int2base(x, base):
    if x < 0:
      sign = -1
    elif x == 0:
      return digs[0]
    else: sign = 1
    x *= sign
    digits = []
    while x:
        digits.append(digs[int(x % base)])
        x /= base
    if sign < 0:
        digits.append('-')
    digits.reverse()
    res = ''.join(digits)
    return res[len(res)-2:]

def componentToHex(c):
    hex = int2base(c,16)
    if len(hex) == 1:
        return "0" + hex
    else:
        return hex

def rgdToHex(r,g,b):
    return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b)


def rgbCalc(b):
    g = math.floor(((5 - b)*1.0/ 5) * 255)
    r = math.floor((b / 5.0) * 255)
    return rgdToHex(r,g,0)

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
            return
        q=ndb.gql("SELECT * FROM Account WHERE email = :1",mail)
        p=q.get()
        if not p:
            self.redirect('/account')
            return
        # lat = 40.442606
        # lng = -79.956686
        lat_long ='('+lat+', ' + lng+')';
        query = Location.query(Location.locationInfo == lat_long)
        location = query.fetch()
        if (not location) or len(location) == 0:
            self.redirect(add)
        else:
            val = 0
            hLatBound = float(lat) + .010
            lLatBound = float(lat) - .010
            hLngBound = float(lng) + .010
            lLngBound = float(lng) - .010
            qry1 = Location.query()
            qry2 = qry1.filter(Location.latitude > lLatBound)
            qry3 = qry2.filter(Location.latitude < hLatBound)
            locality = qry3.fetch()
            l = []
            for k in locality:
                if lLngBound < k.longitude and k.longitude < hLngBound and k.locationInfo != lat_long:
                    l.append(k)
            hr = now_eastern(datetime.datetime.now()).hour
            val = round(location[0].hour_averages[hr].value,2)
            disp_graph = []
            for r in range(0,24,1):
                ampm = ""
                if(r >= 12):
                    ampm = " pm"
                    if r == 12:
                        s = str(12)
                    else:
                        s = str(r-12)
                else:
                    ampm = " am"
                    if r == 0:
                        s = str(12)
                    else:
                        s = str(r)


                disp_graph.append({"label": s+ampm,
                                       "value": location[0].hour_averages[r % 24].value,
                                       "color": rgbCalc(location[0].hour_averages[r % 24].value)})

            comments = location[0].messageList
            ca = []
            graph_color_val = 0
            if (hr - now_eastern(location[0].lastUpdated).hour) < 1 and (hr - now_eastern(location[0].lastUpdated).hour) >= 0:
                graph_color_val = location[0].currentValue
            else:
                graph_color_val = val

            comments.reverse()
            i = 0
            for comment in comments:
                ct = now_eastern(comment.time)
                timedate = ct.strftime('%m/%d/%y')
                timetime = ct.strftime('%I:%M %p')
                ca.append({"user":str(comment.user),
                           "message":comment.message,
                           "date":timedate,
                           "time":timetime})
                i+=1
                if i > 10:
                    break


            lu = now_eastern(location[0].lastUpdated).strftime('%m/%d/%y at %I:%M:%S %p')

            favs = []
            if p.favorite:
                favs = p.favorite
            renderTemplate(self,'static-information-page.html', {
                "graph_val_col": graph_color_val,
                "location_name": location[0].name,
                "location_latlng": lat_long,
                "location_lat": lat,
                "location_lng": lng,
                "title_link": '/account',
                "around": around,
                "about": about,
                "add": add,
                "log": p.name,
                "recentValue": location[0].currentValue,
                "businessValue": val,
                "last_updated": lu,
                "locality": l,
                "ca": ca,
                "favorites": p.favorite,
                "graph": disp_graph
            })


class PostComment(webapp2.RequestHandler):
    def post(self, lat, lng):
        lat_long ='('+lat+', ' + lng+')'
        query = Location.query(Location.locationInfo == lat_long)
        location = query.fetch()
        user=users.get_current_user()
        if not user:
            self.redirect('/')
            return
        mail=user.email()
        q=ndb.gql("SELECT * FROM Account WHERE email = :1",mail)
        p=q.get()
        if not p:
            self.redirect('/account')
            return
        temp= self.request.get("msg")
        if(len(temp)>1 and len(temp)<151):
            mp = MessagePost(parent=location[0].key,user=p.name, time=datetime.datetime.now(), message=self.request.get("msg"))
            ml = len(location[0].messageList)
            location[0].messageList.append(mp)
            location[0].put()
            i = 0
            query = MessagePost.query(ancestor=location[0].key)
            l_ec = query.fetch()
            while ml < len(l_ec):
                query = MessagePost.query(ancestor=location[0].key)
                l_ec = query.fetch()
                if i > 100:
                    break
                i += 1
            self.redirect("/details/"+lat+"/"+lng)

class ProcessForm(webapp2.RequestHandler):
    def post(self):
        user=users.get_current_user()
        if not user:
            self.redirect('/')
            return
        log=user.nickname()
        mail=user.email()
        global around,about,add
        nname = self.request.get('username')
        nhome = ""
        if self.request.get('lat_long') != "undefined" and self.request.get('lat_long') and self.request.get('lat_long')!= '':
            nhome = self.request.get('lat_long')

        q=ndb.gql("SELECT * FROM Account WHERE email = :1", mail)
        p=q.get()
        coord=nhome
        log=nname
        favs = []
        if not p:
            if nhome == "":
                nhome = "(40.442606, -79.956686)"
            u=Account(email=user.email(), name=nname, home=nhome, favorite=[])
            u.put()
        else:
            if nhome != "":
                p.home=nhome
            p.name=nname
            p.put()

            for f in p.favorite:
                query = Location.query(Location.locationInfo == f)
                location = query.fetch()
                if len(location) != 0 and location:
                    favs.append(location[0])

        renderTemplate(self, 'static-search-page.html', {
            "title_link": '/account',
            "favorites": favs,
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
            return
        if not user:
            self.redirect('/')
        mail = user.email()
        q=ndb.gql("SELECT * FROM Account WHERE email = :1",mail)
        p = q.get()
        if not p:
            self.redirect('/account')
            return
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
        user=users.get_current_user()
        if not user:
            self.redirect('/')
            return
        if not user:
            self.redirect('/')
        mail = user.email()
        q=ndb.gql("SELECT * FROM Account WHERE email = :1",mail)
        p = q.get()
        if not p:
            self.redirect('/account')
            return
        name=p.name
        if(not(re.match("^\((-?(?:1[0-7]|[1-9])?\d(?:\.\d{1,18})?|180(?:\.0{1,18})?), (-?(?:1[0-7]|[1-9])?\d(?:\.\d{1,18})?|180(?:\.0{1,18})?)\)",
                        self.request.get('lat_long'))) and len(self.request.get('location_name')) == 0 and
                   len(self.request.get('address')) == 0):
            renderTemplate(self,'static-location-creation-page.html', {
                "title_link": '/account',
                "around": around,
                "add": add,
                "log": name,
                "about": about
            })
            return

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
            ha = []
            loc = Location(lastUpdated=datetime.datetime.now(), currentValue=0, latitude=lat, longitude=lng,
                           locationInfo=lat_long, name=self.request.get('location_name'), messageList=[],
                           businessValues=[], hour_averages=[])
            for i in range(0,24):
                ha.append(HourAnalytic(value=0.0, hour=i, count=0, parent=loc.key))
            loc.hour_averages = ha
            loc.put()
            my_document = search.Document(
                # Setting the doc_id is optional. If omitted, the search service will create an identifier.
                fields=[
                    search.TextField(name='locationInfo',value = lat_long),
                    search.TextField(name='name', value = self.request.get('location_name')),
                    search.TextField(name='address', value= self.request.get('address'))
                ])
            try:
                index = search.Index(name="LocationIndexDoc")
                index.put(my_document)
            except search.Error:
                print("ERROR")
            
        i = 0
        query = Location.query(Location.locationInfo == lat_long)
        location = query.fetch()
        while not location:
            query = Location.query(Location.locationInfo == lat_long)
            location = query.fetch()
            if i > 10:
                self.redirect(around)
            i+=1

        self.redirect('/details/'+str(lat)+'/'+str(lng))


class UpdateAccount(webapp2.RequestHandler):
    def get(self):
        global about
        global around
        global add
        user=users.get_current_user()
        if not user:
            self.redirect('/')
            return
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
            "nickname": nickname,
            "local": local,
            "logout": logout,
            "about": about,
            "around": around,
            "add": add,
            "ll": latlong,
        })

class AboutUs(webapp2.RequestHandler):
    def get(self):
        global about
        global around
        global add
        user=users.get_current_user()
        if not user:
            self.redirect('/')
            return
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
        if not user:
            self.redirect('/')
            return
        mail=user.email()
        if not user:
            self.redirect('/')
        q=ndb.gql("SELECT * FROM Account WHERE email = :1",mail)
        p=q.get()
        if p:
            p.favorite.append("(" + self.request.get("lat") + ", " + self.request.get("lng") + ")")
            p.put()
        else:
            self.redirect('/')




class ContactUs(webapp2.RequestHandler):
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


class UpdateDetails(webapp2.RequestHandler):
    def post(self, lat, lng):
        lat_long ='('+lat+', ' + lng+')'
        query = Location.query(Location.locationInfo == lat_long)
        location = query.fetch()
        user=users.get_current_user()
        if not user:
            self.redirect('/')
            return
        mail=user.email()
        q=ndb.gql("SELECT * FROM Account WHERE email = :1", mail)
        p=q.get()
        if not p:
            self.redirect('/account')
            return

        if (int(self.request.get("crowdlvl")) <6 and int(self.request.get("crowdlvl")) >= 0):
            nw = datetime.datetime.now()
            bv = BusinessValue(parent=location[0].key, value=int(self.request.get("crowdlvl")), time=nw, user=user)
            bl = len(location[0].businessValues)
            location[0].lastUpdated = datetime.datetime.now()
            location[0].currentValue = int(self.request.get("crowdlvl"))
            location[0].businessValues.append(bv)
            logging.warning(str(location[0].hour_averages[int(now_eastern(nw).hour % 24)].value))
            location[0].hour_averages[int(now_eastern(nw).hour % 24)].value = (location[0].hour_averages[int(now_eastern(nw).hour % 24)].count * location[0].hour_averages[int(now_eastern(nw).hour % 24)].value +
                                                              int(self.request.get("crowdlvl")))/(location[0].hour_averages[int(now_eastern(nw).hour % 24)].count+1)
            location[0].hour_averages[int(now_eastern(nw).hour % 24)].count += 1
            logging.warning(str(location[0].hour_averages[int(now_eastern(nw).hour % 24)].count) + " " + str(location[0].hour_averages[int(now_eastern(nw).hour % 24)].value))
            location[0].put()
            query = BusinessValue.query(ancestor=location[0].key)
            l_ec = query.fetch()
            i = 0

            while bl < len(l_ec):
                query = BusinessValue.query(ancestor=location[0].key)
                l_ec = query.fetch()
                if i > 100:
                    break
                i += 1
            self.redirect("/details/"+lat+"/"+lng)
            return
        else:
            self.redirect("/")


class Account(ndb.Model):
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True)
    home = ndb.StringProperty(required=True)
    favorite = ndb.StringProperty(repeated=True)


class BusinessValue(ndb.Model):
    value = ndb.IntegerProperty(required=True)
    user = ndb.UserProperty()
    time = ndb.DateTimeProperty(required=True)

class MessagePost(ndb.Model):
    message = ndb.StringProperty(required=True)
    user = ndb.StringProperty(required=True)
    time = ndb.DateTimeProperty(required=True)

class HourAnalytic(ndb.Model):
    hour = ndb.IntegerProperty(required=True)
    count = ndb.IntegerProperty(required=True)
    value = ndb.FloatProperty(required=True)

class Location(ndb.Model):
    latitude = ndb.FloatProperty(required=True)
    longitude = ndb.FloatProperty(required=True)
    locationInfo = ndb.StringProperty(required=True)
    hour_averages = ndb.StructuredProperty(HourAnalytic, repeated=True)
    lastUpdated = ndb.DateTimeProperty(required=True)
    name = ndb.StringProperty(required=True)
    currentValue = ndb.IntegerProperty(required=True)
    businessValues = ndb.StructuredProperty(BusinessValue, repeated=True)
    messageList = ndb.StructuredProperty(MessagePost, repeated=True)


def now_eastern(tm):
    return datetime.datetime.fromtimestamp(time.mktime(tm.timetuple()), Eastern_tzinfo())

class Eastern_tzinfo(datetime.tzinfo):
    """Implementation of the Es timezone."""
    def utcoffset(self, dt):
        return datetime.timedelta(hours=-5) + self.dst(dt)

    def _FirstSunday(self, dt):
        """First Sunday on or after dt."""
        return dt + datetime.timedelta(days=(6-dt.weekday()))

    def dst(self, dt):
        # 2 am on the second Sunday in March
        dst_start = self._FirstSunday(datetime.datetime(dt.year, 3, 8, 2))
        # 1 am on the first Sunday in November
        dst_end = self._FirstSunday(datetime.datetime(dt.year, 11, 1, 1))

        if dst_start <= dt.replace(tzinfo=None) < dst_end:
            return datetime.timedelta(hours=1)
        else:
            return datetime.timedelta(hours=0)
    def tzname(self, dt):
        if self.dst(dt) == datetime.timedelta(hours=0):
            return "PST"
        else:
            return "PDT"

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/comment/details/([^/]+)/([^/]+)', PostComment),
    ('/post/details/([^/]+)/([^/]+)', UpdateDetails),
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