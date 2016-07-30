
import pickle


class Link(object):
    pass

link1 = Link()
pickle.dump({'a': link1}, open('pick2.out', 'wb'))
