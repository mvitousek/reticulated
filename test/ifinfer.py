import re
value = '169.254/16'
# Items in the list are strings like these: *.local, 
m = re.match(r"(\d+(?:\.\d+)*)(/\d+)?", value)

mask = m.group(2)
if mask is None:
    mask = 8 * (m.group(1).count('.') + 1)
else:
    mask = int(mask[1:])
mask = 32 - mask
