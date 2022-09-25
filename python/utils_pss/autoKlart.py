from pyexcel_ods3 import get_data

sheets = get_data(r"C:\AmDesp\data\AmDespConfig.ods")
clarts_dict = dict()
attrs = sheets['CLASS_ATTRS']
for field in attrs:
    if field:
        k = field[0]
        v = field[1:]
        clarts_dict.update({k: v})
        # (field[0], )



# for clart in sheets['CLASS_ATTRS']:
#     if not clart:
#         print (f"notclat, {clart}")
#         continue
#     k = clart[0]
#     v= clart[1:]
#     clarts.update({k: v})

# with open('C:\AmDesp\data\CLASS_ATTRS.csv','r') as f:
#     clarts = csv.reader(f)
#     for clart in clarts:
#         print(clart)
#
#
#     # type(k,(Product,), {}
#     # types.new_class(m, bases='Product', kwds=None, exec_body=None)
#


# print(type(sheets.items()), '\n', sheets)

# ndata = get_data("test.ods")
# print(json.dumps(ndata))

# from pyexcel_ods3 import save_data
# sheets = OrderedDict()
# sheets.update({"Sheet 1": [[1, 2, 3], [4, 5, 6]]})
# sheets.update({"Sheet 2": [[7, 8, 9], [10, 11, 12]]})
# io = BytesIO()
# save_data(io, sheets)
# # do something with the io
# # In reality, you might give it to your http response
# # object for downloading

# my_list = []

# with open(r'C:\AmDesp\data\test.ods', 'r') as f:
#     reader = csv.reader(f)
#     # for clart in reader:



#
# for attr in attrs:
#     clart = attr[0]
#     class clart:



#
# creating class dynamically

# class ObjFact:
#     def __init__(self, csv):
#
#
# csv_file = r"C:\AmDesp\sheets\test.ods"
# for clart in csv_file:
#     attributes = {}
#     for column in clart[1:]:
#         attributes[column] = ObjFact(column)
#         globals()[clart[0]] = type(clart[0], (Table,), attributes)




###############################

################################


# # constructor
# def constructor(self, arg):
#     self.constructor_arg = arg
# # method
# def displayMethod(self, arg):
#     print(arg)
# # class method
# @classmethod
# def classMethod(cls, arg):
#     print(arg)
#
# # creating class dynamically
# Geeks = type("Geeks", (object,), {
#     # constructor
#     "__init__": constructor,
#
#     # sheets members
#     "string_attribute": "Geeks 4 geeks !",
#     "int_attribute": 1706256,
#
#     # member functions
#     "func_arg": displayMethod,
#     "class_func": classMethod
# })
#
##################
# # creating class dynamically
# Geeks = type("Geeks", (object,), {
#     # constructor
#     "__init__": constructor,
#
#     # sheets members
#     "string_attribute": "Geeks 4 geeks !",
#     "int_attribute": 1706256,
#
#     # member functions
#     "func_arg": displayMethod,
#     "class_func": classMethod
# })
##################
# # creating objects
# obj = Geeks("constructor argument")
# print(obj.constructor_arg)
# print(obj.string_attribute)
# print(obj.int_attribute)
# obj.func_arg("Geeks for Geeks")
# Geeks.class_func("Class Dynamically Created !")

'''
Output:

constructor argument
Geeks 4 geeks!
1706256
Geeks for GeeksClass Dynamically Created!

In the above program, class Geeks is dynamically created which has a constructor. 
The sheets members of Geeks are string_attribute and int_attribute
 member functions of Geeks are displayMethod() and classMethod(). 
 An object obj of class Geeks is created and all the sheets members are assigned and displayed, 
 all the member functions of Geeks are also called.
'''

# get field
