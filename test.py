import os


data = "\\a\\b\\c\\d"
data.replace("\\", "/")
print(data)
l = data.split("/")
print(os.path.join(*l))
