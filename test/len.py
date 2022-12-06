import json

_len="-11000"
_len_ = "".join(list(filter(str.isdigit, _len)))

print(type(_len_))
print(_len_)

print(json.dumps(0))
r=[1]
print(isinstance(r,list))