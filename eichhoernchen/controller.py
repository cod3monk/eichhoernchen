#!/usr/bin/env python
# encoding: utf-8
import re

class UserQuery:
    # Possible operators
    operators = ':=<>!~'
    
    # <key><op><value> regex:
    modifier_regex = r'((?:"[^"]+)"|(?:\S+))(['+re.escape(operators)+'])((?:"[^"]+")|(?:\S+))'

    @staticmethod
    def parse(q):
        """Takes user query string *q* and returns matching PyMongo query."""
    
        # Remove front and end white-spaces:
        q = q.strip()
        
        modifiers = []
        sorters = []
        words = []
        
        # finding modifiers
        while True:
            m = re.search(UserQuery.modifier_regex, q)
            if not m:
                break
            
            g = m.groups()
            
            # Remove quotes from string beginning/end
            g = (g[0].strip('"'), g[1], g[2].strip('"'))
            
            # If modifier key equals "sort", it is treated special:
            if g[0] == "sort":
                sorters.append(g)
            else:
                modifiers.append(g)
            
            # Remove modifier from query string
            q = q[:m.start()]+q[m.end():]
        
        # finding search words
        for m in re.finditer(r'((?:"[^"]+)"|(?:\S+))', q):
            g = m.groups()[0].strip('"')
            words.append(g)
        
        # TODO Return PyMongo query object
        return modifiers, sorters, words

if __name__ == "__main__":
    qs = """
        resistor 0201
        cat:"passiv elements"
        loc:"first drawer"
        loc="Room 5/Shelf 3/Top"
        packaging:0201
        sort:price
        sort:"price desc"
        "max hight"<10
        width>20
        "foo bar" baz loc:Tree cat:Wood sort:weight
        """
    for q in qs.split('\n'):
        print q.strip()
        print UserQuery.parse(q)
        print