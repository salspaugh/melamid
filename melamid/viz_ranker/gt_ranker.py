import numpy as np
import pylab as plt
import threading
from viz_ranker import VizRanker

DIMENSION = 2
NPOINTS = 10

def do_compare(viz1, viz2, viz_ranker, learned_comparison=True, gt_comparison=True):
    better = viz_ranker.closer_point(viz1, viz2, viz_ranker.ground_truth)
    viz_ranker.finish_comparison(viz1, viz2, better, learned_comparison=learned_comparison, gt_comparison=gt_comparison)

class GroundTruthVizRanker(VizRanker):
    def __init__(self, ground_truth, *args, **kwargs):
        super(GroundTruthVizRanker, self).__init__(*args, **kwargs)
        self.ground_truth = ground_truth

    def start_comparison(self, viz1, viz2, learned_comparison=True, gt_comparison=True):
        threading.Thread(target=do_compare, 
                         args=(viz1, viz2, self),
                         kwargs={'learned_comparison': learned_comparison,
                                 'gt_comparison': gt_comparison}).start()

    def draw(self):
        plt.plot([self.ground_truth[0]], [self.ground_truth[1]], 'ro')        
        super(GroundTruthVizRanker, self).draw()

if __name__ == '__main__':
    points = np.around(np.random.rand(NPOINTS, DIMENSION), decimals=4).tolist()
    GROUND_TRUTH = np.around(np.random.rand(DIMENSION), decimals=4)
    viz_ranker = GroundTruthVizRanker(GROUND_TRUTH, points)
    viz_ranker.train()
    viz_ranker.rank_all(get_gt=True)
    viz_ranker.evaluate()
    if DIMENSION == 2:
        viz_ranker.draw()
        plt.show()
