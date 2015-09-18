
from datetime import datetime
from datetime import timedelta



def LastMonth(month, year):
   '''

   >>> LastMonth(8, 2015)
   datetime.datetime(2015, 7, 31, 0, 0)
   >>> LastMonth(1, 2015)
   datetime.datetime(2014, 12, 31, 0, 0)
   >>> LastMonth(3, 2015)
   datetime.datetime(2015, 2, 28, 0, 0)
   '''
   thisMonth = datetime(year, month, 1)
   return thisMonth - timedelta(1)


def NextMonth(month, year):
   '''
   >>> NextMonth(8, 2015)
   datetime.datetime(2015, 9, 1, 0, 0)
   >>> NextMonth(12, 2015)
   datetime.datetime(2016, 1, 1, 0, 0)
   '''
   thisMonth = datetime(year, month, 1)
   # get a day just in the beginning of next month
   nextMonth = thisMonth + timedelta(32)
   # and reset to the first day
   return nextMonth.replace(day=1)


kMonthFormat = "%Y%m"

class Month(object):
   def __init__(self, monthOrStr=None, year=None):
      '''
         We can create a Month object in two ways:
         - passing in the string format that we use in URLs, 'YYYYMM'
         - passing in two integers, month (1..12), year
         >>> this = Month(7, 2015)
         >>> str(this)
         '201507'
         >>> this = Month("201507")
         >>> str(this)
         '201507'
      '''
      if hasattr(monthOrStr, "lower"):
         self.month = datetime.strptime(monthOrStr, kMonthFormat)
      else:
         today = datetime.today()
         month = monthOrStr or today.month
         year = year or today.year
         self.month = datetime(year, month, 1)

   def Next(self):
      '''
      >>> this = Month(9, 2015)
      >>> str(this)
      '201509'
      >>> next = this.Next()
      >>> str(next)
      '201510'
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
      nextMonth = self.month + timedelta(32)
      return Month(nextMonth.month, nextMonth.year)

   def Previous(self):
      prevMonth = self.month - timedelta(1)
      return Month(prevMonth.month, prevMonth.year)

   def __str__(self):
      return self.month.strftime(kMonthFormat)

   def Formatted(self, fmt="%b %Y"):
      '''
      >>> this = Month(9, 2015)
      >>> this.Formatted()
      'Sep 2015'
      >>> this.Formatted("%b")
      'Sep'
      '''

      return self.month.strftime(fmt)

   def __cmp__(self, other):
      return cmp(self.month, other.month)



import doctest
doctest.testmod()
