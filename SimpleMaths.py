def linearMap(from_min,from_max,to_min,to_max,value,clamp=False):
    v=(value-from_min)/(from_max-from_min)*(to_max-to_min)+to_min
    if clamp and v>to_max:
        return to_max
    if clamp and v<to_min:
        return to_min
    return v



