import pymel.core as pm


def get_selected_channels():
    top_attr = pm.channelBox('mainChannelBox', q=True, selectedMainAttributes=True)
    shape_attr = pm.channelBox('mainChannelBox', q=True, selectedShapeAttributes=True)
    input_attr = pm.channelBox('mainChannelBox', q=True, selectedHistoryAttributes=True)
    output_attr = pm.channelBox('mainChannelBox', q=True, selectedOutputAttributes=True)
    
    print top_attr
    print shape_attr
    print input_attr
    print output_attr
    
get_selected_channels()
