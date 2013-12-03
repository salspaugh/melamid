import itertools
import numpy as np
import pylab as plt
import threading

class VizRanker(object):
    """ Base class for ranking visualizations.
    Usage:
      train() trains the model
      rank(viz1, viz2) compares the two visualizations.
      rank_all() precomputes all possible comparisons.
      evaluate() compares inferred comparisons to ground truth.
    """
    def __init__(self, viz_list):
        self.viz_list = viz_list # list of d-dimensional featurized visualizations
        self.dcell = DCell() # region in d-space that contains reference visualization.
        self.learned_comparisons = {}
        self.gt_comparisons = {}
        self.total_cmps = len(viz_list) * (len(viz_list) - 1) / 2.0
        self.generated_cmps = 0
        self.dimension = len(self.viz_list[0])
        self.trained = False
        self.train_iterator = self.active_comparisons()
        self.can_compare_flag = threading.Event()
        self.compare_lock = threading.Lock()
        self.can_compare_flag.set()
        self.gt_populated = False

    def train(self):
        while self.train_next(): continue

    def rank(self, viz1, viz2, get_gt=False):
        if not self.trained:
            raise ValueError("Cannot rank without training model first.")
        cmp_key = self.get_cmp_key(viz1, viz2)
        if cmp_key not in self.learned_comparisons:
            if get_gt:
                self.start_comparison(viz1, viz2, learned_comparison=False, gt_comparison=True)
            self.learned_comparisons[cmp_key] = self.infer_rank(viz1, viz2)
        return self.learned_comparisons[cmp_key]

    def rank_all(self, get_gt=False):
        self.compare_lock.acquire()
        for viz1, viz2 in itertools.combinations(self.viz_list, 2):
            self.rank(viz1, viz2, get_gt=get_gt)
        self.compare_lock.release()

    def finish_comparison(self, viz1, viz2, better_viz, learned_comparison=False, gt_comparison=True):
        try:
            if learned_comparison:
                self.learned_comparisons[self.get_cmp_key(viz1, viz2)] = better_viz
                self.dcell.add_bound(SeparatingHyperPlane(viz1, viz2, better=better_viz))
            if gt_comparison:
                self.gt_comparisons[self.get_cmp_key(viz1, viz2)] = better_viz
            if len(self.gt_comparisons) == self.total_cmps:
                self.gt_populated = True
        finally:
            self.can_compare_flag.set() # we're all done: others can compare now.

    def train_next(self):
        if self.trained:
            return False
        try:
            # Wait until we're done with the comparison.
            self.compare_lock.acquire()
            self.can_compare_flag.wait()
            self.can_compare_flag.clear()
            self.compare_lock.release()
            viz1, viz2 = self.train_iterator.next()
            self.generated_cmps += 1
            self.start_comparison(viz1, viz2, learned_comparison=True, gt_comparison=True)
            return True
        except StopIteration:
            self.trained = True
            print "Total comparisons: %d. Generated comparisons: %d. That's %.2f%%!" % (
                self.total_cmps, self.generated_cmps, 100.0 * float(self.generated_cmps) / self.total_cmps)
            self.can_compare_flag.set() # we're all done: others can compare now.
            return False
        except:
            self.can_compare_flag.set() # Error: make sure to let others compare.
            raise

    def evaluate(self):
        while not self.gt_populated: pass # spin until gt is fully populated.
        success = self.learned_comparisons == self.gt_comparisons
        npoints = len(self.viz_list)
        if not success:
            n_total = self.total_cmps
            n_wrong = 0
            for comp_key in self.learned_comparisons.keys():
                lc = self.learned_comparisons[comp_key] 
                gc = self.gt_comparisons[comp_key]
                if lc != gc:
                    if npoints < 10 and self.dimension < 10:
                        print comp_key, lc, gc
                    n_wrong += 1
            print "error rate: %f" % (float(n_wrong) / n_total)
            if npoints < 10 and self.dimension < 10:
                #print GROUND_TRUTH
                print viz_ranker.dcell.internal_point
        else:
            print "error rate: 0%"
                    
    def infer_rank(self, viz1, viz2):
        if viz1 in self.dcell and viz2 in self.dcell: raise Exception('wtf??')
        if viz1 in self.dcell:
            return viz1
        if viz2 in self.dcell:
            return viz2
        return self.closer_point(viz1, viz2, self.dcell.internal_point)

    def active_comparisons(self):
        for viz1, viz2 in itertools.combinations(self.viz_list, 2):
            if self.is_ambiguous(viz1, viz2):
                yield (viz1, viz2)

    def closer_point(self, point1, point2, reference):
        # returns p1 if p1 is closer to reference than p2, p2 otherwise
        def dist(p1, p2):
            return np.linalg.norm(np.array(p1) - np.array(p2))
        return point1 if dist(point1, reference) < dist(point2, reference) else point2

    def get_cmp_key(self, viz1, viz2):
        # get the same key for either order of comparison
        l1, l2 = sorted([viz1, viz2])

        # just concatenate the lists
        return str(l1) + str(l2)

    def start_comparison(self, viz1, viz2, learned_comparison=True, gt_comparison=True):
        """ Subclasses should implement. This method is asynchronous: i.e., it should return immediately, and 
        eventually call self.finish_comparison(viz1, viz2, better_viz, learned_comparison, gt_comparison). 
        It need not worry about synchronization. learned_comparison and gt_comparison should be passed through
        to finish_comparison with no modification.
        """
        raise NotImplemented

    def is_ambiguous(self, viz1, viz2):
        return self.dcell.intersected_by(SeparatingHyperPlane(viz1, viz2))

    def draw(self):
        # Plot the separated points
        plt.scatter(*(np.array(self.viz_list).T), color='b', marker='o')

        #Plot the dcell
        self.dcell.draw()

        plt.xlim([-2,2])
        plt.ylim([-2,2])
        plt.show(block=False)

class SeparatingHyperPlane(object):
    def __init__(self, p1, p2, better=None):
        self.p1 = np.array(p1)
        self.p2 = np.array(p2)
        self.better = better
        direction = -1 if better == p1 else 1

        # Equation of a hyperplane: n dot (Y - p) = 0
        # we multiply by direction to see which side of the plane we should be on:
        # if direction * n dot (Y - p) > 0, then Y is on the right side of the plane.
        self.normal = direction * (self.p2 - self.p1)
        self.normal = self.normal / np.linalg.norm(self.normal)
        self.intercept = 0.5 * (self.p1 + self.p2)

    def consistent_with(self, p):
        dot_product = np.dot(self.normal, np.array(p) - self.intercept)
        return dot_product > 0 or np.isclose(dot_product, 0.0)

    def draw(self, show=False):
        # Assume 2D, so we can draw lines
        assert len(self.p1) == 2, "Can't draw > 2D hyperplanes!"

        # Plot the line
        if self.normal[1] == 0:
            x_i = self.intercept[0]
            y = np.arange(x_i - 100, x_i + 100, 0.01)
            x = [x_i]*len(y)
        else:
            x = np.arange(-100, 100, 0.01)
            y = [((-self.normal[0] * (x_i - self.intercept[0])) / self.normal[1]) 
                 + self.intercept[1]
                 for x_i in x]
        plt.plot(x, y, 'b')

        # Plot the normal
        normal_t = np.arange(0, 1, 0.01)
        normal_xy = [self.intercept + normal_ti * self.normal for normal_ti in normal_t]
        plt.plot(*(np.array(normal_xy).T), color='g')

        if show:
            plt.show()

class DCell(object):
    def __init__(self):
        self.planes = []
        self.internal_point = None # a point in the region, for reference

    def __contains__(self, point):
        for plane in self.planes:
            if not plane.consistent_with(point):
                return False
        return True

    def add_bound(self, hyperplane):
        self.planes.append(hyperplane)

    def compute_intersection(self, hyperplane1, hyperplane2):
        # Write the intersection of two hyperplanes in Ax = b form.
        # [n1, n2]^T * X = [n1 dot p1, n2 dot p2]^T
        A = np.vstack([hyperplane1.normal, hyperplane2.normal])
        b = np.array([np.dot(hyperplane1.normal, hyperplane1.intercept),
                      np.dot(hyperplane2.normal, hyperplane2.intercept)])
        try:
            x = np.linalg.solve(A, b)
            return x
        except np.linalg.LinAlgError as e:
            return None # no intersection: hyperplanes are parallel.

    def intersected_by(self, hyperplane):
        # a new hyperplane h intersects the dcell if the dcell contains a hyperplane d such that:
        #   * d intersects with h
        #   * any point on the intersection of d and h is contained in the d cell.
        # or if the dcell is empty
        if not self.planes:
            dimension = len(hyperplane.normal)
            self.internal_point = np.around(np.random.rand(dimension), decimals=4)
            return True
        
        for dcell_plane in self.planes:
            intersection = self.compute_intersection(dcell_plane, hyperplane)
            if intersection == None:
                # hyperplanes are parallel, no solution.
                # we can test any point on the new hyperplane to see if there's an intersection.
                # so let's test the intercept we're already storing!
                if hyperplane.intercept in self:
                    self.internal_point = hyperplane.intercept
                    return True
            else:
                # We got an intersection. Test if it lies in the d cell.
                if intersection in self:
                    self.internal_point = intersection
                    return True                
        return False

    def draw(self, show=False):
        for p in self.planes:
            p.draw()
        plt.plot([self.internal_point[0]], [self.internal_point[1]], 'rs')
        if show:
            plt.show()




