import inspect
from pprint import pprint

# local namespace
print(inspect.currentframe().f_locals)

# next outer frame object (this frame’s caller)
print(inspect.currentframe().f_back)

# sourcecode line
pprint(inspect.currentframe().f_lineno)
