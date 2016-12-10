import maya.cmds as cmds


def fix_shapes():
    all_geos = cmds.ls(sl=True)
    counter = 0  ### moved counter outside loop
    for geo in all_geos:
        shapes = cmds.listRelatives(geo, fullPath=True, shapes=True)

        if len(shapes) == 1:
            continue

        listing = []  ### fixed naming, was new_listing, not coherent
        listing.append(shapes[:1])
        # pop out the first shape, since we don't have to fix it
        multi_shapes = shapes[1:]
        for multi_shape in multi_shapes:
            new_transform = cmds.duplicate(multi_shape, parentOnly=True)
            new_geos = cmds.parent(multi_shape, new_transform, addObject=True, shape=True)
            listing.append(new_geos)

            # remove the shape from its original transform
            cmds.parent(multi_shape, removeObject=True, shape=True)

        # counter to 'version' up new_geos group naming
        new_group_name = cmds.group(em=True, name='TEST_' + str(counter + 1) + '_GRP')

        counter += 1  ### simpler way to increment instead of "counter = counter + 1"

        for item in listing:  ### fixed new_listing name here as well
            new_geos_parent_name = cmds.listRelatives(item, parent=True)
            cmds.parent(new_geos_parent_name, new_group_name)


fix_shapes()