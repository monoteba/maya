import pymel.core as pm


def undoable(function):
    """
     :return: return function
    """
    
    def undoFunction(*args, **kwargs):
        pm.undoInfo(openChunk=True)
        functionReturn = None
        try:
            functionReturn = function(*args, **kwargs)
        
        except:
            print pm.sys.exc_info()[1]
        
        finally:
            pm.undoInfo(closeChunk=True)
            return functionReturn
    
    return undoFunction
