import os
import webapp2
from google.appengine.ext.webapp import template


def render_template(handler, templatename, templatevalues) :
  path = os.path.join(os.path.dirname(__file__), 'templates/' + templatename)
  html = template.render(path, templatevalues)
  handler.response.out.write(html)

  
class MainPage(webapp2.RequestHandler) :
  def post(self):
    self.response.out.write('<HTML><BODY>Hello, that\'s a post</BODY></HTML>')
    
  def get(self):
    name = "Mr. Cui"
    template_params = {
      "name": name
    }
    render_template(self, 'index.html', template_params)
    

app = webapp2.WSGIApplication([
  ('/', MainPage)
])




