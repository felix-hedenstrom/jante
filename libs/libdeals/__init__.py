#!/usr/bin/env python3
# -*- coding: utf-8 -*-

if __name__ == '__main__':
    # file executed directly, can do direct imports (even if executed from outside own directory!)
    # ... but need to add path to typecheck lib
    import sys
    sys.path.append("..")
    
    from deal import deal
    from source import source
elif __package__ == '':
    # file imported in relative manner, need to add own directory to path
    import sys
    import os.path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from deal import deal
    from source import source
else:
    # file imported in absolute manner, we can do relative imports on package contents
    from .deal import deal
    from .source import source
