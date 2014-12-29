"""
A list of specific licence versions, which actually aren't necessary if we just use substring
searches on the url roots
    ("http://creativecommons.org/licenses/by/4.0", "cc-by"),
    ("http://creativecommons.org/licenses/by-nd/4.0", "cc-by-nd"),
    ("http://creativecommons.org/licenses/by-sa/4.0", "cc-by-sa"),
    ("http://creativecommons.org/licenses/by-nc/4.0", "cc-by-nc"),
    ("http://creativecommons.org/licenses/by-nc-nd/4.0", "cc-by-nc-nd"),
    ("http://creativecommons.org/licenses/by-nc-sa/4.0", "cc-by-nc-sa"),
    ("http://creativecommons.org/licenses/by/3.0", "cc-by"),
    ("http://creativecommons.org/licenses/by-nd/3.0", "cc-by-nd"),
    ("http://creativecommons.org/licenses/by-sa/3.0", "cc-by-sa"),
    ("http://creativecommons.org/licenses/by-nc/3.0", "cc-by-nc"),
    ("http://creativecommons.org/licenses/by-nc-nd/3.0", "cc-by-nc-nd"),
    ("http://creativecommons.org/licenses/by-nc-sa/3.0", "cc-by-nc-sa"),
    ("http://creativecommons.org/licenses/by/2.0", "cc-by"),
    ("http://creativecommons.org/licenses/by-nd/2.0", "cc-by-nd"),
    ("http://creativecommons.org/licenses/by-sa/2.0", "cc-by-sa"),
    ("http://creativecommons.org/licenses/by-nc/2.0", "cc-by-nc"),
    ("http://creativecommons.org/licenses/by-nc-nd/2.0", "cc-by-nc-nd"),
    ("http://creativecommons.org/licenses/by-nc-sa/2.0", "cc-by-nc-sa"),
"""

# The urls in the order that they should be searched for
urls = [
    ("http://creativecommons.org/licenses/by-nc-nd", "cc-by-nc-nd"),
    ("http://creativecommons.org/licenses/by-nc-sa", "cc-by-nc-sa"),
    ("http://creativecommons.org/licenses/by-nd", "cc-by-nd"),
    ("http://creativecommons.org/licenses/by-sa", "cc-by-sa"),
    ("http://creativecommons.org/licenses/by-nc", "cc-by-nc"),
    ("http://creativecommons.org/licenses/by", "cc-by"),
]
substrings = urls