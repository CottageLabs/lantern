from copy import deepcopy

# Functions for helping us make good lists of licence strings to normalise

def make_variation_map(parts, target):
    d = {}

    # lowercase first
    [d.update({v : target}) for v in make_variations([p.lower() for p in parts])]

    # then upper case
    [d.update({v : target}) for v in make_variations([p.upper() for p in parts])]

    return d

def make_variations(parts):
    parts.reverse()
    sep = [[" " if s == "0" else "-" for s in list('0'*(6 - len(bin(i))) + bin(i)[2:])] for i in range(2**(len(parts) - 1))]
    vars = []
    for s in sep:
        s.reverse()
        var = []
        for i in range(len(parts)):
            var.append(parts[i])
            if i != len(parts) - 1:
                var.append(s[i])
        var.reverse()
        vars.append("".join(var))
    return vars


# the possible types we'll see in EPMC, and the canonical type they map to
types = {}
types.update(make_variation_map(["cc"], "cc"))
types.update(make_variation_map(["cc", "by"], "cc-by"))
types.update(make_variation_map(["cc", "by", "sa"], "cc-by-sa"))
types.update(make_variation_map(["cc", "by", "nd"], "cc-by-nd"))
types.update(make_variation_map(["cc", "by", "nc"], "cc-by-nc"))
types.update(make_variation_map(["cc", "by", "nc", "nd"], "cc-by-nc-nd"))
types.update(make_variation_map(["cc", "by", "nc", "sa"], "cc-by-nc-sa"))

# some types which are regularly mis-represented
types.update(make_variation_map(["cc", "nc"], "cc-by-nc"))
types.update(make_variation_map(["cc", "nc", "nd"], "cc-by-nc-nd"))

# The urls in the order that they should be searched for, and the type they map to
urls = [
    ("http://creativecommons.org/licenses/by-nc-nd", "cc-by-nc-nd"),
    ("http://creativecommons.org/licenses/by-nc-sa", "cc-by-nc-sa"),
    ("http://creativecommons.org/licenses/by-nd", "cc-by-nd"),
    ("http://creativecommons.org/licenses/by-sa", "cc-by-sa"),
    ("http://creativecommons.org/licenses/by-nc", "cc-by-nc"),
    ("http://creativecommons.org/licenses/by", "cc-by"),
]

# The substrings in the order that they should be searched for, and they type they map to
# (currently just look for the urls, we're not going to try and do any string analysis)
substrings = deepcopy(urls)
substrings.extend([
    ('CC-BY-NC-ND', 'cc-by-nc-nd'),
    ('CC BY-NC-ND', 'cc-by-nc-nd'),
    ('CC BY NC ND', 'cc-by-nc-nd'),
    ('Creative Commons Attribution-NonCommercial-No deriv', 'cc-by-nc-nd'),
    ('Creative Commons Attribution-NonCommercial-NoDeriv', 'cc-by-nc-nd'),
    ('Creative Commons Attribution NonCommercial-No deriv', 'cc-by-nc-nd'),
    ('Creative Commons Attribution NonCommercial-NoDeriv', 'cc-by-nc-nd'),
    ('Creative Commons Attribution NonCommercial No deriv', 'cc-by-nc-nd'),
    ('Creative Commons Attribution NonCommercial NoDeriv', 'cc-by-nc-nd'),
    ('Creative Commons Attribution - NonCommercial - No deriv', 'cc-by-nc-nd'),
    ('Creative Commons Attribution - NonCommercial - NoDeriv', 'cc-by-nc-nd'),
    ('Creative Commons Attribution NonCommercial - No deriv', 'cc-by-nc-nd'),
    ('Creative Commons Attribution NonCommercial - NoDeriv', 'cc-by-nc-nd'),
    ('CC-BY-NC-SA', 'cc-by-nc-sa'),
    ('CC BY-NC-SA', 'cc-by-nc-sa'),
    ('CC BY NC SA', 'cc-by-nc-sa'),
    ('Creative Commons Attribution-NonCommercial-Share Alike', 'cc-by-nc-sa'),
    ('Creative Commons Attribution-NonCommercial-ShareAlike', 'cc-by-nc-sa'),
    ('Creative Commons Attribution NonCommercial-Share Alike', 'cc-by-nc-sa'),
    ('Creative Commons Attribution NonCommercial-ShareAlike', 'cc-by-nc-sa'),
    ('Creative Commons Attribution NonCommercial Share Alike', 'cc-by-nc-sa'),
    ('Creative Commons Attribution NonCommercial ShareAlike', 'cc-by-nc-sa'),
    ('Creative Commons Attribution - NonCommercial - Share Alike', 'cc-by-nc-sa'),
    ('Creative Commons Attribution - NonCommercial - ShareAlike', 'cc-by-nc-sa'),
    ('Creative Commons Attribution NonCommercial - Share Alike', 'cc-by-nc-sa'),
    ('Creative Commons Attribution NonCommercial - ShareAlike', 'cc-by-nc-sa'),
    ('CC-BY-NC', 'cc-by-nc'),
    ('CC BY-NC', 'cc-by-nc'),
    ('CC BY NC', 'cc-by-nc'),
    ('Creative Commons Attribution-NonCommercial', 'cc-by-nc'),
    ('Creative Commons Attribution-Non Commercial', 'cc-by-nc'),
    ('Creative Commons Attribution NonCommercial', 'cc-by-nc'),
    ('Creative Commons Attribution Non Commercial', 'cc-by-nc'),
    ('Creative Commons Attribution - NonCommercial', 'cc-by-nc'),
    ('Creative Commons Attribution - Non Commercial', 'cc-by-nc'),
    ('CC-BY-ND', 'cc-by-nd'),
    ('CC BY-ND', 'cc-by-nd'),
    ('CC BY ND', 'cc-by-nd'),
    ('Creative Commons Attribution-No deriv', 'cc-by-nd'),
    ('Creative Commons Attribution-NoDeriv', 'cc-by-nd'),
    ('Creative Commons Attribution No deriv', 'cc-by-nd'),
    ('Creative Commons Attribution NoDeriv', 'cc-by-nd'),
    ('Creative Commons Attribution - No deriv', 'cc-by-nd'),
    ('Creative Commons Attribution - NoDeriv', 'cc-by-nd'),
    ('CC-BY-SA', 'cc-by-sa'),
    ('CC BY-SA', 'cc-by-sa'),
    ('CC BY SA', 'cc-by-sa'),
    ('Creative Commons Attribution-Share Alike', 'cc-by-sa'),
    ('Creative Commons Attribution-ShareAlike', 'cc-by-sa'),
    ('Creative Commons Attribution Share Alike', 'cc-by-sa'),
    ('Creative Commons Attribution ShareAlike', 'cc-by-sa'),
    ('Creative Commons Attribution - Share Alike', 'cc-by-sa'),
    ('Creative Commons Attribution - ShareAlike', 'cc-by-sa'),
    ('CC-BY', 'cc-by'),
    ('CC BY', 'cc-by'),
    ('Creative Commons Attribution', 'cc-by'),
    ('CC0', 'cc0')
])

