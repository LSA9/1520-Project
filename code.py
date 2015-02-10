import os
import webapp2
from google.appengine.ext.webapp import template


def renderTemplate(handler, templatename, templatevalues) :
    path = os.path.join(os.path.dirname(__file__), 'templates/' + templatename)
    html = template.render(path, templatevalues)
    handler.response.out.write(html)


class MainPage(webapp2.RequestHandler) :
    def get(self) :
        renderTemplate(self,'static-login-page.html', {})


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
                                  ('/processform',ProcessForm)
                              ], debug=True)