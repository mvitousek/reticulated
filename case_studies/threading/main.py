from threading import *

num_profiles = 0

def profile_func(x,y,z):
    global num_profiles
    num_profiles += 1

setprofile(profile_func)

def run_func(x, y, z):
    print('running thread, args: ')
    print(x)
    print(y)
    print(z)

thread = Thread(target=run_func, args=(1,2,3))

thread.start()

thread.join()

print(num_profiles)
