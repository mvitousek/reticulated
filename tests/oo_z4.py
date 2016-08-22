def counted(x):
    return x

@fields({'my_dict': Dict(Int, Tuple(Int, Int))})
class UnionFind:
    #this doesn't need to be here
    @counted
    def __init__(self:'UnionFind', my_dict:Dict(Int, Tuple(Int, Int)))->Void:
        self.my_dict = my_dict

    @counted
    def add_node(self:'UnionFind', n:Int)->Void:
        self.my_dict[n] = (n, 0)

    @counted
    def find(self:'UnionFind', n:Int)->Tuple(Int, Int):
        if self.my_dict[n][0] != n:
            self.my_dict[n] = self.find(self.my_dict[n][0])
        return self.my_dict[n]

    @counted
    def union(self:'UnionFind', l1:Tuple(Int, Int), l2:Tuple(Int, Int))->Void:
        k1 = l1[0]
        k2 = l2[0]
        r1 = l1[1]
        r2 = l2[1]
        if r1 < r2:
            self.my_dict[k1] = l2
        elif r1 > r2:
            self.my_dict[k2] = l1
        else:
            self.my_dict[k2] = l1
            self.my_dict[k1] = (self.my_dict[k1][0], r1+1)

UnionFind({})
