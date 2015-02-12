import os
import webapp2
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import db


def renderTemplate(handler, templatename, templatevalues) :
    path = os.path.join(os.path.dirname(__file__), 'templates/' + templatename)
    html = template.render(path, templatevalues)
    handler.response.out.write(html)


class MainPage(webapp2.RequestHandler) :
  def get(self) :
	user=users.get_current_user()
	global around
	global about
	title_link=''
	title=''
	type=''
	message=''
	log=''
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
	"title": title,
	"log": log,
	"title_link" : title_link,
	"about": about
	})
	#self.response.out.write("<html><body>%s</body></html>" % greeting)
	
class SearchPage(webapp2.RequestHandler):
	def get(self) :
		global about
		global around
		title_link=(users.create_logout_url('/'))
		user=users.get_current_user()
		if user:
			log=user.nickname()
		else:
			log='Please login'
			self.redirect('/')
		renderTemplate(self,'static-search-page.html', {
		"title_link": title_link,
		"around": around,
		"message": log,
		"about": about
	
	})
	
class DetailsPage(webapp2.RequestHandler):
	def get(self):
		global about
		global around
		title_link=(users.create_logout_url('/'))
		user=users.get_current_user()
		if user:
			log=user.nickname()
		else:
			log='Please login'
			self.redirect('/')
		renderTemplate(self,'static-information-page.html', {
		"name": 'test',
		"title_link": title_link,
		"around":around,
		"about":about,
		"log":log
		
		})
		
class ProcessForm(webapp2.RequestHandler):
    def post(self):
        name = self.request.get('name')
        color = self.request.get('color')
        renderTemplate(self, 'formresult.html', {
        "name": name,
        "color": color,
		
        })		
		
class Account(db.Model):
			name= db.StringProperty(required=True)
			email=db.StringProperty(required=True)
			home=db.GeoPtProperty(required=True)
		
app = webapp2.WSGIApplication([
	('/', MainPage),
	('/details',DetailsPage),
	('/search',SearchPage),
	('/processform',ProcessForm)
	], debug=True)	

around='/search'
about='/details'
