#!/usr/bin/env python
# encoding: utf-8
import re

class UserQuery:
    # Possible operators
    operators = ':=<>!~'
    
    # <key><op><value> regex:
    modifier_regex = r'((?:"[^"]+)"|(?:\S+))(['+re.escape(operators)+']=?)((?:"[^"]+")|(?:\S+))'
    
    # The mongodb language to be used for searches
    language = 'english'

    @staticmethod
    def parse(q, limit=100):
        """Takes user query string *q* and returns matching mongodb text query."""
    
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
                sorters.append(g[2])
            else:
                modifiers.append(g)
            
            # Remove modifier from query string
            q = q[:m.start()]+q[m.end():]
        
        # finding search words
        for m in re.finditer(r'((?:"[^"]+)"|(?:\S+))', q):
            words.append(m.groups()[0])
        
        # TODO Return PyMongo query object, plus sorters
        # Something like: {"date": {"$lt": d}}, sorters
        filter_ = {}
        
        for key, op, value in modifiers:
            if op == '=':
                filter_[key] = value
            elif op == ':':
                filter_[key] = value
            elif op == '!':
                if key in filter_:
                    filter_[key]["$ne"] = value
                else:
                    filter_[key] = {"$ne": value}
            elif op == '<':
                if key in filter_:
                    filter_[key]["$lt"] = value
                else:
                    filter_[key] = {"$lt": value}
            elif op == '<=':
                if key in filter_:
                    filter_[key]["$lte"] = value
                else:
                    filter_[key] = {"$lte": value}
            elif op == '>':
                if key in filter_:
                    filter_[key]["$gt"] = value
                else:
                    filter_[key] = {"$gt": value}
            elif op == '>=':
                if key in filter_:
                    filter_[key]["$gte"] = value
                else:
                    filter_[key] = {"$lte": value}
            elif op == '~':
                filter_[key] = {"$regex": value}
            else:
                # No match, so we use key and value as normal words
                word.append(key)
                words.append(value)
        
        return {'search': ' '.join(words), 
                'filter': filter_, 
                'language': UserQuery.language,
                'limit': limit}, sorters

if __name__ == "__main__":
    qs = """
        resistor 0201
        cat:"passiv elements"
        loc:"first drawer"
        loc="Room 5/Shelf 3/Top"
        packaging:0201
        sort:price
        sort:"price desc"
        "max height"<10
        width>20
        "foo bar" baz loc:Tree cat:Wood sort:weight
        """
    for q in qs.split('\n'):
        print q.strip()
        print UserQuery.parse(q)
        print