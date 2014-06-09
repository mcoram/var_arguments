debug=False # Optionally turn on debug print statements
## To test, use "nosetests -v var_arguments.py"

"""
"""

def recon_dict(dictToImitate,dictWithValues):
    """
    recon_dict is for the case when you have one dictionary that holds old values
    for all the keys that you're interested in, and another dictionary that holds the
    new values for all those keys (as well as possibly others that you don't want)
    """
    return dict( (k,dictWithValues[k]) for k in dictToImitate.keys() )

def test_recon_dict_1():
    xyab=dict(x=1,y=2,a=3,b=4)
    assert recon_dict(dict(a=8,b=9),xyab)==dict(a=3,b=4)
def test_recon_dict_2():
    old_d=dict(a=8,b=9) # I want these keys, but they're old values
    xyab=dict(x=1,y=2,a=3,b=4) # These are the new values, but I don't want all of them
    new_d=recon_dict(old_d,xyab)
    assert new_d==dict(a=3,b=4)
    

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

def lddict(varstr,dictlist,sep=','):
    """
    Suppose you have dicts xy=dict(x=1,y=2) and ab=dict(a=3,b=4).
    And that what you would normally write is:
       dict(x=xy['x'],b=ab['b'])
    in order to get dict(x=1,b=4), in this case.
    Now you can write: lddict('x,b',[xy,ab]), to get the same result
    """
    varl=varstr.split(sep)
    revdlist=dictlist[:]
    revdlist.reverse()
    result={}
    for k in varl:
        found=False
        for d1 in revdlist:
            if d1.has_key(k):
                result[k]=d1[k]
                found=True
                break
        if not found:
            raise KeyError(k)
    return result

def test_lddict_1():
    xy=dict(x=1,y=2)
    ab=dict(a=3,b=4)
    answer=dict(x=xy['x'],b=ab['b'])
    assert answer==dict(x=1,b=4)
    assert answer==lddict('x,b',[xy,ab])
    x=5
    assert lddict('x,b',[xy,ab,locals()]) == dict(x=5,b=4)
    try:
        lddict('z,b',[xy,ab])
    except KeyError, e:
        None # Expected; there's no z
    else:
        assert False
        
        
    
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
    return f(**lddict(varstr,dictlist))

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
    If you want this trick to work when you pass, e.g. dargs=[locals()], or, generally,
    if the dictionaries in the dargs list have extra keys that are not arguments of f,
    write f to accept **kwargs as an argument.
    """
    def f_new(*pargs,**kwargs):
        dargs=kwargs.get('dargs',None)
        if dargs!=None:
            nargs={}
            if debug: print 'dargs==%r'%dargs
            for d in dargs:
                nargs.update(d)
            del kwargs['dargs']
            nargs.update(kwargs) # let keyword arguments override even the dargs dictionaries
            return f(*pargs,**nargs)
        else:
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

    # To test precedence overriding, let the locals and ab have extraneous values for a
    # the intended result is that the "a=3" in the call takes precedence
    ab['a']=7
    a=8
    yd={'y':2}
    assert use_dargs(fA)(1,a=3,dargs=[yd,ab])==4
    assert use_dargs(fB)(1,a=3,dargs=[locals(),ab])==4

    # Here we're testing that the value for a should come from ab
    ab['a']=3
    assert use_dargs(fB)(1,dargs=[yd,ab])==4
    assert use_dargs(fB)(1,dargs=[locals(),ab])==4
    

def dict_return(f):
    """
    Decorator that composes the function with a call to lddict.
    """
    def f_new(*pargs,**kwargs):
        varstr,yourdicts=f(*pargs,**kwargs)
        return lddict(varstr,yourdicts)
    return f_new

def test_decorators():
      def myfunc_mundane(x,y,a,b):
          y=x+a
          return dict(x=x,y=y,a=a,b=b)

      answer=myfunc_mundane(1,2,3,4)
      assert answer==dict(x=1,y=4,a=3,b=4)

      @dict_return
      @use_dargs
      def myfunc(x,y,a,b):
          y=x+a
          return 'x,y,a,b',[locals()]


      ab={'a':3,'b':4}
      xy={'x':1,'y':2}
      assert myfunc(1,2,3,4) == answer
      assert myfunc(1,2,dargs=[ab]) == answer
      assert myfunc(dargs=[ab,xy]) == answer
      assert myfunc(dargs=[xy,ab]) == answer
      justb={'b':4}
      assert myfunc(a=3,dargs=[xy,justb]) == answer

def test_stack_overflow_solution():
    def f_mundane(d1,d2):
        x,y,a,b = d1['x'],d1['y'],d2['a'],d2['b']
        y=x+a
        return {'x':x,'y':y}, {'a':a,'b':b}

    def f(d1,d2):
        r=f2(dargs=[d1,d2])
        return recon_dict(d1,r), recon_dict(d2,r)

    @use_dargs
    def f2(x,y,a,b):
        y=x+a
        return locals()

    xy=dict(x=1,y=2)
    ab=dict(a=3,b=4)
    answer_xy, answer_ab=f_mundane(xy,ab)
    assert answer_xy==dict(x=1,y=4)
    assert answer_ab==dict(a=3,b=4)

    res_xy, res_ab = f(xy,ab)
    assert res_xy==answer_xy
    assert res_ab==answer_ab

    answer=dict(x=1,y=4,a=3,b=4)
    assert f2(1,2,3,4)==answer
    assert f2(1,a=3,dargs=[dict(y=2,b=4)])==answer
    assert f2(dargs=[dict(x=1,y=2),dict(a=3,b=4)])==answer

def experimental_idiom(f):
    return dict_return(use_dargs(f))

def test_experimental_idiom():

    @experimental_idiom
    def f1(u):
        z=u+5
        x=z+5
        y=z+6
        xz=ddict('x,z',locals())
        return 'x,y,xz',[locals()]

    @experimental_idiom
    def f2(a,u,y,**kwargs):
        a=(u-1)*y
        return 'a,y',[locals()]
    d1=dict(u=0)
    d2=f1(dargs=[d1])
    d3=f2(a=7,dargs=[d1,d2])
    
__all__=["recon_dict", "ddict", "lddict", "dcall", "ldcall", "use_dargs", "dict_return","experimental_idiom"]
