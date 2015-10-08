


class DictTupleAdapter(object):
   ''' Class to convert between a dict to a tuple and then back again. Useful when 
      we have Mongo records coming back that we want to temprarily insert into 
      a set() (which requires elements that are hashable).
   '''

   def __init__(self, *fields):
      self.fields = fields

   def DictToTuple(self, d):
      '''
      >>> dta = DictTupleAdapter('a', 'b', 'c')
      >>> d1 = {'a': 1, "b": 2, "c": 3}
      >>> dta.DictToTuple(d1)
      (1, 2, 3)
      '''

      return tuple([d[f] for f in self.fields])

   def TupleToDict(self, t):
      '''

      >>> dta = DictTupleAdapter('a', 'b', 'c')
      >>> d1 = {'a': 1, "b": 2, "c": 3}
      >>> t = dta.DictToTuple(d1)
      >>> d2 = dta.TupleToDict(t)
      >>> d1 == d2
      True
      '''
      assert len(t) == len(self.fields)
      retval = {}
      for field, val in zip(self.fields, t):
         retval[field] = val

      return retval


if __name__ == "__main__":
   import doctest
   doctest.testmod()

