
from datetime import datetime
from datetime import timedelta



kMonthFormat = "%Y%m"

class Month(object):
   def __init__(self, monthOrStr=None, year=None):
      '''
         We can create a Month object in three ways:
         - passing in a datetime.datetime object
         - passing in the string format that we use in URLs, 'YYYYMM'
         - passing in two integers, month (1..12), year
         >>> this = Month(7, 2015)
         >>> str(this)
         '201507'
         >>> this = Month("201507")
         >>> str(this)
         '201507'
      '''
      if hasattr(monthOrStr, "today"):
         self._month = monthOrStr
      elif hasattr(monthOrStr, "lower"):
         self._month = datetime.strptime(monthOrStr, kMonthFormat)
      else:
         today = datetime.today()
         month = monthOrStr or today.month
         year = year or today.year
         self._month = datetime(year, month, 1)

   @property 
   def year(self):
      return self._month.year

   @property
   def month(self):
      return self._month.month

   def Next(self, count=1):
      '''
      >>> this = Month(9, 2015)
      >>> str(this)
      '201509'
      >>> next = this.Next()
      >>> str(next)
      '201510'
      >>> str(this.Next(2))
      '201511'
      >>> str(this.Next(0))
      '201509'
      >>> str(this.Next(-1))
      '201508'
      >>> str(this.Previous())
      '201508'
      >>> this = Month(12, 2015)
      >>> next = this.Next()
      >>> str(next)
      '201601'
      >>> prev = next.Previous()
      >>> str(prev)
      '201512'
      '''
      if 0 == count:
         return self
      elif count < 0:
         return self.Previous(count * -1)
      else:
         nextMonth = self._month + timedelta(32)
         nextMonth = Month(nextMonth.month, nextMonth.year)
         if 1 == count:
            return nextMonth
         else:
            return nextMonth.Next(count-1)

   def Previous(self, count=1):
      if 0 == count:
         return self
      elif count < 0:
         return self.Next(-1 * count)
      else:
         prevMonth = self._month - timedelta(1)
         prevMonth = Month(prevMonth.month, prevMonth.year)
         if 1 == count:
            return prevMonth
         else:
            return prevMonth.Previous(count-1)

   def __str__(self):
      return self._month.strftime(kMonthFormat)

   def Formatted(self, fmt="%b %Y"):
      '''
      >>> this = Month(9, 2015)
      >>> this.Formatted()
      'Sep 2015'
      >>> this.Formatted("%b")
      'Sep'
      '''

      return self._month.strftime(fmt)


   def Range(self, other):
      '''
      Calculate the span of months between two Month objects.
      >>> this = Month(9, 2015)
      >>> other = Month(10, 2015)
      >>> this.Range(other)
      1
      >>> this.Range(Month(11, 2015))
      2
      >>> this = Month(2, 2015)
      >>> this.Range(Month(11, 2014))
      3
      >>> Month(1, 2015).Range(Month(4, 2015))
      3
      >>> Month(2, 2015).Range(Month(3, 2015))
      1
      >>> Month(2, 2015).Range(Month(4, 2015))
      2
      >>> Month(3, 2015).Range(Month(3, 2015))
      0
      '''
      if other >= self:
         dayDelta = other._month - self._month
         # Add 3 extra days to catch problems around Feb being short.
         monthDelta = (dayDelta.days + 3) / 30
      else:
         return other.Range(self)

      return monthDelta


   def __cmp__(self, other):
      return cmp(self._month, other._month)



import doctest
doctest.testmod()
