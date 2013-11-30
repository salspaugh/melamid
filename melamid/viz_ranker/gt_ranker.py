import numpy as np
import pylab as plt
from viz_ranker import VizRanker

DIMENSION = 2
NPOINTS = 10

class GroundTruthVizRanker(VizRanker):
    def __init__(self, ground_truth, *args, **kwargs):
        super(GroundTruthVizRanker, self).__init__(*args, **kwargs)
        self.ground_truth = ground_truth

    def get_comparison(self, viz1, viz2):
        return self.closer_point(viz1, viz2, self.ground_truth)

    def draw(self):
        plt.plot([self.ground_truth[0]], [self.ground_truth[1]], 'ro')        
        super(GroundTruthVizRanker, self).draw()

if __name__ == '__main__':
    points = np.around(np.random.rand(NPOINTS, DIMENSION), decimals=4).tolist()
    GROUND_TRUTH = np.around(np.random.rand(DIMENSION), decimals=4)
    viz_ranker = GroundTruthVizRanker(GROUND_TRUTH, points)
    viz_ranker.rank_all(get_gt=True)
    viz_ranker.evaluate()
    if DIMENSION == 2:
        viz_ranker.draw()
        plt.show()
