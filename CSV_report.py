import csv
import string
import re
import sys
import pycountry
from collections import namedtuple
from datetime import datetime
from ftfy import fix_text
from operator import attrgetter


Record = namedtuple('Record', 'date, state, impressions, CTR')
RecordCountry = namedtuple('RecordCountry', 'date, country, impressions, CTR')

class Reporter():
  '''
  Input format: UTF-8 or UTF-16 CSV file (with any kind of line endings), with columns: date
  (MM/DD/YYYY), state name, number of impressions and CTR percentage.

  Output format: UTF-8 CSV file with Unix line endings, with columns: date (YYYY-MM-DD),
  three letter country code (or XXX for unknown states), number of impressions, number of
  clicks (rounded, assuming the CTR is exact). Rows are sorted lexicographically by date
  followed by the country code.
  '''
  def __init__(self):
    self.Records = []

  def isFormatOk(self,row):
    """
    Check if provided data has right format.
    If not return False.
    Wrong format is when:
    data is not in (MM/DD/YYYY) convension,
    impresions < 0,
    CTR is out of <0-1> range
    """
    try:
      date = datetime.strptime(row[0], "%m/%d/%Y").date()
      state = fix_text(row[1])
      impressions = int(row[2])
      if impressions < 0:
        raise ValueError
      CTR = float(row[3].replace("%",""))
      if CTR < 0 or CTR > 1:
        raise ValueError
    except ValueError as e:
      print(f"Wrong format of provided data {row}", file=sys.stderr)
      pass
      return False
    return Record(date=date, state=state, impressions=impressions, CTR=CTR)
    
  def loadReport(self,filename):
    """
    Load data from UTF-8 or UTF-16 CSV file (with any kind of line endings), with columns: date
    (MM/DD/YYYY), state name, number of impressions and CTR percentage.
    """
    with open(filename, encoding='utf-8-sig') as f:
      reader = csv.reader(f)
      try:
        for row in reader:
          formated = self.isFormatOk(row)
          print(formated)
          if formated:
            self.Records.append(formated)
      except csv.Error as e:
        sys.exit('file {}, line {}: {}'.format(filename, reader.line_num, e))

  def findCountryCode(self):
    """
    Change state into country code
    records change their data type
    """
    RecordsWithCountry = []
    for state in pycountry.subdivisions:
      #print(state.name)
      for record in self.Records:      
        if state.name == record.state:
          print(state.country, record.state)
          r = RecordCountry(date=record.date,
                            country=state.country.alpha_3,
                            impressions=record.impressions,
                            CTR=record.CTR)
          self.Records.remove(record)
          RecordsWithCountry.append(r)
    for record in self.Records: 
      print(record)
      r = RecordCountry(date=record.date,
                            country="XXX",
                            impressions=record.impressions,
                            CTR=record.CTR)
      RecordsWithCountry.append(r)
    self.Records = RecordsWithCountry

  def reformat(self):
    self.Records.sort(key=attrgetter('country'))
    self.Records.sort(key=attrgetter('date'))
    lastDate, impresions, clicks, country = None, 0, 0, ""
    print(len(self.Records))
    for record in self.Records:
      #print(record)
      if country and (record.date != lastDate or record.country != country):
        print(lastDate, country, impresions, round(clicks/100))
        impresions = 0
        clicks = 0
      lastDate = record.date
      impresions += record.impressions
      clicks +=record.impressions*record.CTR
      country = record.country
    print(lastDate, country, impresions, round(clicks/100))


if __name__ == "__main__":
  r = Reporter()
  r.loadReport("raport.csv")
  r.findCountryCode()
  r.reformat()


