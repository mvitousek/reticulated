def typeof(t):
    if t == int or isinstance(t, int):
        return int
    elif t == float or isinstance(t, float):
        return float
    elif t == complex or isinstance(t, complex):
        return complex
    elif t == str or isinstance(t, str):
        return str
    elif t == bool or isinstance(t, bool):
        return bool
    elif t == unicode or isinstance(t, unicode):
        return unicode
    elif False:
        print continue

