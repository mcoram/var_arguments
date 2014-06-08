debug=False # Optionally turn on debug print statements
## To test, use "nosetests -v var_arguments.py"

"""
Here are some tricks to remove the redundancy of mentioning variable names multiple times within a function body. First, we can change:
  {'x':x,'y':y}
into:
  ddict('x,y',locals())

...ddict...

Similary, we can change:
  f(x=x,y=y)
into:
  dcall(f,'x,y',locals())
where:

...dcall...

More generally, if we have a dictionary xy with keys x and y and if our local variables include a and b, we can change:
  f(x=xy['x'],y=xy['y'],a=a,b=b)
into:
  ldcall(f,'x,y,a,b',[locals(),xy])
where:

...ldcall...
(If keys are defined in multiple dictionaries, the behavior will be that the later dictionaries override the former; make sure that's what you want.)

"""

def ddict(varstr,yourlocals,sep=','):
    """
    Select the subset of a dictionary corresponding to the keys named in a string
    example: ddict('a,c',dict(a=1,b=2,c=3))==dict(a=1,c=3)
    note: interesting when applied to a dictionary of the callers local variables
    example:
    
      def foo(c):
        a=c-2;b=2
        return ddict('a,c',locals())
      assert foo(3) == dict(a=1,c=3)
    """
    return dict( (k,yourlocals[k]) for k in varstr.split(sep) )

def test_ddict_1():
    assert ddict('a,c',dict(a=1,b=2,c=3))==dict(a=1,c=3)
def test_ddict_2():
    def foo(c):
        a=c-2;b=2
        return ddict('a,c',locals())
    assert foo(3) == dict(a=1,c=3)    

def dcall(f,varstr,yourlocals):
    """
    Let's you change: f(x=x,y=y)
      into:
    dcall(f,'x,y',locals())
    """
    return f(**ddict(varstr,yourlocals))

def test_dcall_1():
    def f(a=None,b=None,c=None):
        assert a==1 and c==3 and b==None
    a=1;b=2;c=3
    dcall(f,'a,c',locals())

def ldcall(f,varstr,dictlist):
    """
    Suppose you have a dictionary xy with keys x and y and local variables a and b, then
    we can change:
      f(x=xy['x'],y=xy['y'],a=a,b=b)
    into:
      ldcall(f,'x,y,a,b',[locals(),xy])
    (If keys are defined in multiple dictionaries, the behavior will be that the later
     dictionaries override the former; make sure that's what you want.)
    """
    merged_dict={}
    for d in dictlist: merged_dict.update(d)
    return f(**ddict(varstr,merged_dict))

def test_ldcall():
      def f(x,y,a,b):
          assert x==1 and y==2 and a==3 and b==4
      xy=dict(x=1,y=2)
      x=None # should be overridden
      a=3;b=4
      f(x=xy['x'],y=xy['y'],a=a,b=b)
      ldcall(f,'x,y,a,b',[locals(),xy])
      ldcall(f,'x,a,y,b',[locals(),xy])

def use_dargs(f):
    """
    Decorator that allows a function to accept arguments via an optional dargs
    keyword argument that, if present, must be a list of dictionaries.
    The key value pairs in those dictionaries will appear as regular arguments
    to the decorated function.
    If you want think trick to work when you pass, e.g. dargs=[locals()], write the
    function to accept **kwargs as an argument.
    """
    def f_new(*pargs,**kwargs):
        dargs=kwargs.get('dargs',None)
        if dargs!=None:
            if debug: print 'dargs==%r'%dargs
            del kwargs['dargs']
            for d in dargs:
                kwargs.update(d)
        return f(*pargs,**kwargs)
    return f_new

def test_use_dargs_1():
    def fA(x,y,a,b):
        assert x==1 and y==2 and a==3 and b==4
        return x+a
    def fB(x,y,a,b,**kwargs):
        assert x==1 and y==2 and a==3 and b==4
        return x+a

    assert use_dargs(fA)(1,2,3,4) == 4 #1A
    assert use_dargs(fB)(1,2,3,4) == 4 #1B
    
    xy=dict(x=1,y=2)
    ab=dict(a=3,b=4)
    assert use_dargs(fA)(dargs=[xy,ab]) == 4 #2A
    assert use_dargs(fB)(dargs=[xy,ab]) == 4 #2B
    
    y=2
    bd={'b':4}
    try:
        assert use_dargs(fA)(1,a=3,dargs=[locals(),bd]) == 4 #3A
    except TypeError:
        None ## A TypeError that complains "got an unexpected keyword argument 'bd'" is expected
    else:
        assert False
    assert use_dargs(fB)(1,a=3,dargs=[locals(),bd]) == 4 #3B

    #for 1 and 2, it suffices that f has dargs as a keyword argument.
    #for 3, f will receive the other locals too, like bd, so in order that it ignore
    # such extra arguments, it's necessary that f accept general **kwargs.

def local_return(f):
    """
    Decorator that composes the function with a call to ddict.
    """
    def f_new(*pargs,**kwargs):
        varstr,yourlocals=f(*pargs,**kwargs)
        return ddict(varstr,yourlocals)
    return f_new

def test_decorators():
      def myfunc_mundane(x,y,a,b):
          y=x+a
          return dict(x=x,y=y,a=a,b=b)

      answer=myfunc_mundane(1,2,3,4)
      assert answer==dict(x=1,y=4,a=3,b=4)

      @local_return
      @use_dargs
      def myfunc(x,y,a,b):
          y=x+a
          return 'x,y,a,b',locals()


      ab={'a':3,'b':4}
      xy={'x':1,'y':2}
      assert myfunc(1,2,3,4) == answer
      assert myfunc(1,2,dargs=[ab]) == answer
      assert myfunc(dargs=[ab,xy]) == answer
      assert myfunc(dargs=[xy,ab]) == answer
      justb={'b':4}
      assert myfunc(a=3,dargs=[xy,justb]) == answer
