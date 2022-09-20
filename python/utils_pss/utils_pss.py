# change case
# camel

# blah = "one lc string"
# # pascal

x="'delivery tel'"
y="'delivery tel'"
def MakePascal(x):
    x=x.title()
    for y in x:
        if not y.isalpha():
            if not y.isnumeric():
                x = x.replace(y,'')
    return x



def to_camel_case(text):
    s = text.replace("-", " ").replace("_", " ")
    s = s.split()
    return s[0] + ''.join(i.capitalize() for i in s[1:])
