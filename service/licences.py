# the possible types we'll see in EPMC, and the canonical type they map to
types = {
    "cc" : "cc",
    "cc by" : "cc-by",
    "cc-by" : "cc-by",
    "cc by sa" : "cc-by-sa",
    "cc-by sa" : "cc-by-sa",
    "cc by-sa" : "cc-by-sa",
    "cc-by-sa" : "cc-by-sa",
    "cc by nd" : "cc-by-nd",
    "cc-by nd" : "cc-by-nd",
    "cc by-nd" : "cc-by-nd",
    "cc-by-nd" : "cc-by-nd",
    "cc by nc" : "cc-by-nc",
    "cc-by nc" : "cc-by-nc",
    "cc by-nc" : "cc-by-nc",
    "cc-by-nc" : "cc-by-nc",
    "cc by nc nd" : "cc-by-nc-nd",
    "cc-by nc nd" : "cc-by-nc-nd",
    "cc by-nc nd" : "cc-by-nc-nd",
    "cc by nc-nd" : "cc-by-nc-nd",
    "cc-by-nc nd" : "cc-by-nc-nd",
    "cc by-nc-nd" : "cc-by-nc-nd",
    "cc-by nc-nd" : "cc-by-nc-nd",
    "cc-by-nc-nd" : "cc-by-nc-nd",
    "cc by nc sa" : "cc-by-nc-sa",
    "cc-by nc sa" : "cc-by-nc-sa",
    "cc by-nc sa" : "cc-by-nc-sa",
    "cc by nc-sa" : "cc-by-nc-sa",
    "cc-by-nc sa" : "cc-by-nc-sa",
    "cc by-nc-sa" : "cc-by-nc-sa",
    "cc-by nc-sa" : "cc-by-nc-sa",
    "cc-by-nc-sa" : "cc-by-nc-sa"
}

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
substrings = urls