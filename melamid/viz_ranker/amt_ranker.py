from viz_ranker import VizRanker
import mturk_web_server

from boto.mturk.connection import MTurkConnection
from boto.mturk.question import ExternalQuestion
from boto.mturk.price import Price
from datetime import timedelta
from urllib import urlencode
import threading
import os
import numpy as np
import matplotlib.pyplot as plt
import base64

DIMENSION = 2
NPOINTS = 3
REQUIRED_VOTES = 1
PORT = 8005

def get_amt_connection():
    ACCESS_KEY = 'AKIAIIXWLVTHB64S5RNQ'
    SECRET_KEY= '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'
    HOST = 'mechanicalturk.sandbox.amazonaws.com'
    return MTurkConnection(aws_access_key_id=ACCESS_KEY,
                           aws_secret_access_key=SECRET_KEY,
                           host=HOST)

class AMTPointRanker(VizRanker):
    def __init__(self, ground_truth, *args, **kwargs):
        super(AMTPointRanker, self).__init__(*args, **kwargs)
        self.ground_truth = ground_truth
        self.votes = {}
        self.vote_lock = threading.Lock()

        # start the webserver
        self.webserver_thread = threading.Thread(target=mturk_web_server.run_server, 
                                                 kwargs={'port': PORT,
                                                         'viz_ranker': self})
        self.webserver_thread.daemon = True # Kill the server once we're done.
        self.webserver_thread.start()

    def start_comparison(self, viz1, viz2, learned_comparison=True, gt_comparison=True):
        # create new hit, return
        # generate images for the visualizations, save to disk.
        url_data = {'img_file': self.build_interface_img(viz1, viz2),
                    'cmp_key': self.get_cmp_key(viz1, viz2)}
        self.votes[self.get_cmp_key(viz1, viz2)] = {
            'viz1': (viz1, 0),
            'viz2': (viz2, 0),
            'learned_comparison': learned_comparison,
            'gt_comparison': gt_comparison,
            'finalized': False,
        }
        question = ExternalQuestion(external_url='https://localhost:8005?' + urlencode(url_data),
                                    frame_height=800)
        conn = get_amt_connection()
        conn.create_hit(question=question, title='Testing Hello World', 
                        description='example hit to see if I can use the python API!', 
                        reward=Price(amount=0.03), duration=timedelta(minutes=10),
                        max_assignments=REQUIRED_VOTES, approval_delay=0)

    def add_vote(self, cmp_key, vote):
        if cmp_key not in self.votes:
            raise ValueError('got vote for invalid comparison: %s' % cmp_key)
        try:
            self.vote_lock.acquire()
            vote_info = self.votes[cmp_key]
            if vote_info['finalized']: # we're already done with this one
                return
            vote_key = 'viz1' if vote == 'blue' else 'viz2'
            other_key = 'viz2' if vote == 'blue' else 'viz1'
            vote_viz, vote_counter = vote_info[vote_key]
            vote_counter += 1
            vote_info[vote_key] = (vote_viz, vote_counter)
            other_viz, other_counter = vote_info[other_key]
            if vote_counter + other_counter >= REQUIRED_VOTES:
                winner = vote_viz if vote_counter >= other_counter else other_viz
                vote_info['finalized'] = True
                self.finish_comparison(vote_viz, other_viz, winner, 
                                       learned_comparison=vote_info['learned_comparison'],
                                       gt_comparison=vote_info['gt_comparison'])
        finally:
            self.vote_lock.release()

    def build_interface_img(self, viz1, viz2):
        filename = self.cmp_to_imgfile(viz1, viz2)
        if os.path.exists(filename):
            return filename
        plt.clf()
        plt.plot([viz1[0]], [viz1[1]], 'bo')
        plt.plot([viz2[0]], [viz2[1]], 'go')
        plt.plot([self.ground_truth[0]], [self.ground_truth[1]], 'ro')
        plt.xlim([0, 1])
        plt.ylim([0, 1])
        plt.savefig(filename)
        plt.clf()
        return filename

    def cmp_to_imgfile(self, viz1, viz2):
        file_id = base64.urlsafe_b64encode(self.get_cmp_key(viz1, viz2))
        return 'static/img/cmp_%s.png' % file_id

    def draw(self):
        plt.plot([self.ground_truth[0]], [self.ground_truth[1]], 'ro')
        super(AMTPointRanker, self).draw()

class AMTVizRanker(VizRanker):
    def __init__(self, *args, **kwargs):
        super(AMTVizRanker, self).__init__(*args, **kwargs)

    def start_comparison(self, viz1, viz2, learned_comparison=True, gt_comparison=True):
        # create new hit, return
        url_params = {
            viz
        }        

if __name__ == '__main__':
    points = np.around(np.random.rand(NPOINTS, DIMENSION), decimals=4).tolist()
    GROUND_TRUTH = np.around(np.random.rand(DIMENSION), decimals=4)
    viz_ranker = AMTPointRanker(GROUND_TRUTH, points)
    viz_ranker.train()
    viz_ranker.rank_all(get_gt=True)
    viz_ranker.evaluate()
    viz_ranker.draw()
    plt.show()
