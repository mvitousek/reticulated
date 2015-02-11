import pickle

file = open('pickling.out', 'wb')
pickle.dump("hello world", file)
file.close()
file = open('pickling.out', 'rb')
print(pickle.load(file))
file.close()
