See: http://stackoverflow.com/questions/1897623/unpacking-a-passed-dictionary-into-the-functions-name-space-in-python

I wrote a Python package called var_arguments for conveniently bundling and unbundling arguments that should be useful here; it's available [on github](https://github.com/mcoram/var_arguments).

Instead of writing, say:

    def f(d1,d2):
        x,y,a,b = d1['x'],d1['y'],d2['a'],d2['b']
        y=x+a
        return {'x':x,'y':y}, {'a':a,'b':b}

You could write:

    from var_arguments import recon_dict, use_dargs

    def f(d1,d2):
      r=f2(dargs=[d1,d2])
      return recon_dict(d1,r), recon_dict(d2,r)

    @use_dargs
    def f2(x,y,a,b):
      y=x+a
      return locals()

I wrote the solution like this to match what you seem to be going for: the dictionaries arrive and leave in groups and we minimize the number of times we mention the names of the keys in the dictionaries and/or manually access them. Specifically, we only need to mention x,y,a, and b once this way.

How it works, basically, is that @use_dargs modifies f2 so that it accepts an optional dargs keyword argument, which, if present, should supply a list of dictionaries (dargs=[d1,d2]). The key/value
pairs in those dictionaries are added to the keyword arguments that are otherwise supply to the call to the function, with the keyword arguments having highest priority, d2 having second highest, and
d1 having lowest priority. Accordingly you can call f2 in various ways and get the same result:

    f2(1,2,3,4)
    f2(1,a=3,dargs=[dict(y=2,b=4)])
    f2(dargs=[dict(x=1,y=2),dict(a=3,b=4)])

recon_dict is for the case when you have one dictionary that holds old values
for all the keys that you're interested in, and another dictionary that holds the
new values for all those keys (as well as possibly others that you don't want). For example:

    old_d=dict(a=8,b=9) # I want these keys, but they're old values
    xyab=dict(x=1,y=2,a=3,b=4) # These are the new values, but I don't want all of them
    new_d=recon_dict(old_d,xyab)
    assert new_d==dict(a=3,b=4)

Here are some additional tricks to remove the redundancy of mentioning variable names multiple times within a function body that var_arguments handles.
First, we can change:

    {'x':x,'y':y}

into:

    ddict('x,y',locals())

Similary, we can change:

    f(x=x,y=y)

into:

    dcall(f,'x,y',locals())

More generally, if we have a dictionary xy with keys x and y and if our local variables include a and b, we can change:

    f(x=xy['x'],y=xy['y'],a=a,b=b)

into:

    ldcall(f,'x,y,a,b',[locals(),xy])

