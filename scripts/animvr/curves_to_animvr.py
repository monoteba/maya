import pymel.core as pm
import json


class CurvesToAnimVR:
    """
    Class for converting Maya curves for use in AnimVR as drawn lines
    """
    
    def __init__(self):
        # make data structure available in class
        self.data_structure = []
    
    def get_top_groups(self):
        """
        Only get the top-most groups in the selection to avoid duplicates, since we traverse down
        :return: list
        """
        groups = pm.ls(sl=True, type='transform')
        groups = filter(self.is_group, groups)
        
        groups_filtered = []
        for grp in groups:
            if grp.getParent() not in groups:
                groups_filtered.append(grp)
        
        return groups_filtered
    
    def create_data_structure(self):
        """
        Create the data structure that we'll export later.
        :return: None
        """
        top_groups = self.get_top_groups()
        depth = 0
        
        self.data_structure = []
        
        for group in top_groups:
            self.get_data_for_group(group, depth)
    
    def get_data_for_group(self, group, depth):
        """
        Recursive function for getting all child groups and their curves. Each pass is saved in the data_structure
        :return: None
        """
        # add data for the current group
        curves = self.get_curves(group)  # tuple of isLinear and curve points
        data = {
            'name':         group.nodeName(),
            'depth':        depth,
            'linear': curves[0],
            'curves': curves[1]
        }
        self.data_structure.append(data)
        
        # use recursion to travel through all child groups
        for child in filter(self.is_group, group.getChildren()):
            if child is not None:
                self.get_data_for_group(child, depth + 1)
    
    def get_curves(self, group):
        """
        Get a list of lists with points for each curve.
        :param group: The group to get the curves from.
        :return: list
        """
        
        curves = []
        for child in group.getChildren():
            try:
                if child.getShape().nodeType() == 'nurbsCurve':
                    curves.append(child)
            except AttributeError:
                pass
        
        # get list of points in a list
        is_curve_linear = []
        curve_points = []
        for curve in curves:
            points = self.get_curve_points(curve)
            if points:
                print points[0]
                is_curve_linear.append(points[0])
                curve_points.append(points[1])
        
        return (is_curve_linear, curve_points)
    
    def create_file(self):
        """
        Convert the data structure to JSON and save a file with the data.
        :return: None
        """
        path = pm.fileDialog2(fileFilter="*.avrl", dialogStyle=2, fileMode=0,
                              dir=pm.workspace.path)
        if path:
            self.create_data_structure()
            
            if not self.data_structure:
                pm.warning('No curve data found. Select 1 or more groups containing curves.')
                return
            
            json_data = json.dumps(self.data_structure)
            
            path = path[0]
            f = open(path, 'w+')
            f.write(json_data)
            f.close()
            
            print('\n// File saved as %s' % path),
    
    @staticmethod
    def is_group(node):
        """
        Determine if the specified node is a group. Used with filter(). Empty groups also returns False.
        :param node: Maya node
        :return: bool
        """
        children = node.getChildren()
        
        if not children:
            return False
        
        for child in children:
            if type(child) is not pm.nodetypes.Transform:
                return False
        
        return True
    
    @staticmethod
    def get_curve_points(curve, samples=16):
        """
        Get a sampled list of points on the curve. Sampling takes the curve's length into account.
        :param curve: the curve to create points from
        :param samples: number of steps between edit points
        :return: list
        """
        try:
            if curve.degree() < 1:
                pm.warning('Skipped "%s" because its curve degree is less than 1' % curve.name())
                return None
        except RuntimeError:
            pm.warning('Skipped %s because it is invalid' % curve.name())
            return None
        
        try:
            isLinear = curve.degree() == 1
            points = []
            if isLinear:
                for cv in curve.getCVs(space='world'):
                    points.append(list(cv))
            
            else:
                length = curve.length()
                max_param = curve.findParamFromLength(length)
                step_size = 1.0 / (samples / length)
                step = curve.findParamFromLength(0)
                # print('%s %d samples' % (curve.name(), max_param / step_size))
                
                while step < max_param:
                    points.append(list(curve.getPointAtParam(step, space='world')))
                    step = step + step_size
                
                points.append(list(curve.getPointAtParam(max_param, space='world')))
            
            return (isLinear, points)
        
        except RuntimeError:
            print('\n// Error on %s' % curve.name()),
            return None


if __name__ == '__main__':
    CurvesToAnimVR().create_file()
