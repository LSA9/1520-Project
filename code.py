import os
import webapp2
from google.appengine.ext.webapp import template
from google.appengine.api import users


def renderTemplate(handler, templatename, templatevalues) :
 path = os.path.join(os.path.dirname(__file__), 'templates/' + templatename)
 html = template.render(path, templatevalues)
 handler.response.out.write(html)

class MainPage(webapp2.RequestHandler) :
  def get(self) :
	user=users.get_current_user()
	if user:
		title_link=(users.create_logout_url('/'))
		message=("Welcome, %s" % (user.nickname()))
		title='Welcome'
		log='Logout'
		type='#'
		
	else:
		type=(users.create_login_url('/search'))
		title_link=type
		message= ("Click to login")
		title="Login"
		log='Please Login'
	renderTemplate(self,'static-login-page.html', {
	"link": type,
	"message": message,
	"title": title,
	"log": log,
	"title_link" : title_link
	})
	#self.response.out.write("<html><body>%s</body></html>" % greeting)
	
class SearchPage(webapp2.RequestHandler):
	def get(self)
	title_link=(users.create_logout_url('/'))
	log='Logout'
	
	renderTemplate(self,'static_search_page.html'{
	"title_link": title_link,
	"log": log
	
	})
	
	
	
	
class ProcessForm(webapp2.RequestHandler):
  def post(self):
    name = self.request.get('name')
    color = self.request.get('color')
    renderTemplate(self, 'formresult.html', {
	  "name": name,
	  "color": color
    }) 
	
app = webapp2.WSGIApplication([
  ('/', MainPage),
  ('/search',SearchPage),
  ('/processform',ProcessForm)
], debug=True)	