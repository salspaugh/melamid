import web
from web.wsgiserver import CherryPyWSGIServer as WSGI
import sys

WSGI.ssl_certificate = "server.crt"
WSGI.ssl_private_key = "server.key"

render = web.template.render('templates/')
urls = (
    '/', 'index'
)
global VIZ_RANKER
VIZ_RANKER = None

def run_server(port=8080, viz_ranker=None):
    global VIZ_RANKER
    VIZ_RANKER = viz_ranker
    app = VizRankerApplication(urls, globals())
    app.run(port=port)

class index:
    def GET(self):
        img_url = web.input(img_file='bogus!').img_file
        cmp_key = web.input(cmp_key='bogus!').cmp_key
        assignment_id = web.input(assignmentId='ASSIGNMENT_ID_NOT_AVAILABLE').assignmentId
        allow_submit = assignment_id != 'ASSIGNMENT_ID_NOT_AVAILABLE'
        return render.index(img_url, cmp_key, assignment_id, allow_submit)

    def POST(self):
        answer = web.input(answer=None).answer
        cmp_key = web.input(cmp_key='bogus!').cmp_key
        print answer
        print cmp_key
        VIZ_RANKER.add_vote(cmp_key, answer)

class VizRankerApplication(web.application):
    def run(self, port=8080, *middleware):
        func = self.wsgifunc(*middleware)
        return web.httpserver.runsimple(func, ('0.0.0.0', port))

# Possible flows
# 1. On execution, run webserver, begin alg, create 1st HIT. Periodically poll for results, and 
# create next HIT when enough data comes in.
#
# 2. Proactively capture data via webserver, autolaunch next HIT as appropriate.
#
# Either way, how to deal with main thread? Block until HITs come in (bad?) or write data to disk
# and re-launch on HIT submission. Or add ranker as webserver state?
#
# How to save state? Pickle vizranker, add state for current place in iterator.
