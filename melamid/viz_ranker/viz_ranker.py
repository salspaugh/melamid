import itertools
import numpy as np
import pylab as plt

class VizRanker(object):
    def __init__(self, viz_list):
        self.viz_list = viz_list # list of d-dimensional featurized visualizations
        self.dcell = DCell() # region in d-space that contains reference visualization.
        self.learned_comparisons = {}
        self.gt_comparisons = {}
        self.trained = False
        self.total_cmps = len(viz_list) * (len(viz_list) - 1) / 2.0
        self.dimension = len(self.viz_list[0])

    def rank(self, viz1, viz2, get_gt=False):
        if not self.trained:
            self.train()
        cmp_key = self.get_cmp_key(viz1, viz2)
        if cmp_key not in self.learned_comparisons:
            if get_gt:
                self.gt_comparisons[cmp_key] = self.get_comparison(viz1, viz2)
            self.learned_comparisons[cmp_key] = self.infer_rank(viz1, viz2)
        return self.learned_comparisons[cmp_key]

    def rank_all(self, get_gt=False):
        for viz1, viz2 in itertools.combinations(self.viz_list, 2):
            self.rank(viz1, viz2, get_gt=get_gt)

    def train(self):
        if self.trained:
            return
        generated_cmps = 0
        for viz1, viz2 in self.active_comparisons():
            generated_cmps += 1
            better_viz = self.get_comparison(viz1, viz2)
            self.learned_comparisons[self.get_cmp_key(viz1, viz2)] = better_viz
            self.gt_comparisons[self.get_cmp_key(viz1, viz2)] = better_viz
            self.dcell.add_bound(SeparatingHyperPlane(viz1, viz2,
                                                      better=better_viz))
        print "Total comparisons: %d. Generated comparisons: %d. That's %.2f%%!" % (
            self.total_cmps, generated_cmps, 100.0 * float(generated_cmps) / self.total_cmps)
        self.trained = True

    def evaluate(self):
        success = self.learned_comparisons == self.gt_comparisons
        if not success:
            n_total = self.total_cmps
            n_wrong = 0
            for comp_key in self.learned_comparisons.keys():
                lc = self.learned_comparisons[comp_key] 
                gc = self.gt_comparisons[comp_key]
                if lc != gc:
                    if NPOINTS < 10 and DIMENSION < 10:
                        print comp_key, lc, gc
                    n_wrong += 1
            print "error rate: %f" % (float(n_wrong) / n_total)
            if NPOINTS < 10 and DIMENSION < 10:
                print GROUND_TRUTH
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

    def get_comparison(self, viz1, viz2):
        """ Subclasses should implement! """
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




