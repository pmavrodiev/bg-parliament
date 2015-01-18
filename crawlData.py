#!/usr/bin/python
# -*- coding: utf-8 -*- 

import sys,time, getopt, pickle
import math
import datetime as dt
import mechanize
import lxml.html
import urllib
import re
from os.path import isfile
  

PROGRAM_NAME = "crawlData.py"
BASE_LINK="http://parliament.bg"

class Mp:
  def __init__(self,mp_id):
    self.isgov=False #true if issuer is the government, i.e. министерски съвет
    self.mp_id=mp_id
    self.profession=''
    self.languages=''
    self.name=''
    self.party=''
    self.partyPercentage=0.0
    self.election_area=''
    self.previous_participation={}
    self.html=''
    self.photo='' #link to photo
    self.birth_date=dt.datetime(3000,1,1)
  def printMp():
    
    print "[MP_ID] - " + self.mp_id    
    print "[MP_NAME] - " + self.name
    print "[IS_GOV] - " + self.isgov
    print "[BIRTH_DATE] - " + self.birth_date
    print "[PROFESSION] - " + self.profession
    print "[LANGUAGES] - " + self.languages
    print "[PARTY] - " + self.party
    print "[PARTY_PERCENTAGES] - " + str(self.partyPercentage)
    print "[ELECTION_AREA] - " + self.election_area
    print "[PREVIOUS_PARTICIPATION] - " + self.previous_participation
  
  def encode():
    self.profession=self.profession.encode('utf-8')
    self.languages=self.languages.encode('utf-8')
    self.name=self.name.encode('utf-8')
    self.party=self.party.encode('utf-8')
    self.election_area=self.election_area.encode('utf-8')
    self.html=self.html.encode('utf-8')
    
class Bill:
  def __init__(self,bill_id):
    self.bill_id=bill_id
    self.bill_name='' #име на законопроекта
    self.signature='' #сигнатура
    #init date
    self.date=dt.date(3000,1,1) #дата на постъпване 
    self.session=''
    #contains links to files containing the text of the bill
    self.text=[]
    self.issuers=[]
    self.commission=[] #разпределение по комисии
    self.reports=[] #доклади от комисии
    self.chronology={} #хронология
    self.islaw=False
    #the rest is only for bills that passed as laws
    self.status=''
    self.date_passed=dt.date(3000,1,1) #дата на приемане
    self.when_published='' #обнародван в държавен вестник, пример: 'брой 103/2014 г.'
  def __cmp__(self,otherBill):
    return self.date < otherBill.date
  def __hash__(self):
    return hash(self.bill_id)
  def encode(self):
    self.bill_name=self.bill_name.encode('utf-8')
    self.session=self.session.encode('utf-8')
    for i in self.issuers:
      i.encode()
   

br=mechanize.Browser()
br.set_handle_robots(False)


def getComissionText(link):
  try:
     response=br.open(link)
  except (mechanize.HTTPError, mechanize.URLError) as e:
     print(e)
     return ''
  data=response.get_data()
  html=data.decode('utf-8')
  #read the html source into an lxml object
  root=lxml.html.fromstring(html)
  #get the photo
  result_table=root.xpath('//div[@class="markcontent"]')
  return result_table[0].text_content()

#example: getMp('Министерски съвет','http://www.government.bg/')
def getMp(lii_name,lii_link):
  newMp = Mp('')
  gov="Министерски съвет"
  gov=gov.decode('utf-8')
  if lii_link.find('http://www.government.bg') == 0 or lii_name.find(gov)==0:
     newMp.name=lii_name.encode('utf-8')
     newMp.isgov=True
     return newMp
  newMp.mp_id=lii_link
  newMp.name=lii_name.encode('utf-8')
  try:
     response=br.open(BASE_LINK+lii_link)
  except (mechanize.HTTPError, mechanize.URLError) as e:
     print(e)
     return newMp
  data=response.get_data()
  html=data.decode('utf-8')
  #read the html source into an lxml object
  root=lxml.html.fromstring(html)
  #get the photo
  result_table=root.xpath('//div[@class="MPBlock_columns2"]')
  newMp.photo=result_table[0].getchildren()[0].values()[0] #the link to the photo
  f=urllib.urlretrieve(BASE_LINK+newMp.photo,filename="images/"+newMp.photo.replace("/","-")[1:])
  #  
  result_table=root.xpath('//div[@class="MPinfo"]/ul')
  result_table=result_table[0]
  for li in result_table.getchildren():
    if "Дата на раждане".decode('utf-8') in li.text_content():
      newMp.birth_date=dt.datetime.strptime(re.findall(r'[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}', li.text_content())[0],'%d/%m/%Y')
    elif "Професия".decode('utf-8') in li.text_content():
      newMp.profession=li.text_content().split(':')[1].strip().encode('utf-8')
    elif "Езици".decode('utf-8') in li.text_content():
      newMp.languages=li.text_content().split(':')[1].strip().encode('utf-8')
    elif "Избран".decode('utf-8') in li.text_content():
      newMp.party = re.findall(r'\W+',li.text_content().split(":")[1].strip())[0].encode('utf-8')
      newMp.partyPercentage=float(re.findall(r'\d+.\d+',li.text_content().split(":")[1].strip())[0])
    elif "Изборен".decode('utf-8') in li.text_content():
      newMp.election_area = li.text_content().split(":")[1].strip().encode('utf-8')
    elif "Участие".decode('utf-8') in li.text_content():
      for lii in li.getchildren():
        newMp.previous_participation[lii.values()[0]]=lii.text_content().strip().encode('utf-8')
  newMp.html=html.encode('utf-8')
  return newMp
  
  
def getNewBill(href_link,referenceTitle,billID):
   invalidBill=Bill(-1)
   theBill=Bill(billID)
   try:
     response=br.open(BASE_LINK+href_link)
   except (mechanize.HTTPError, mechanize.URLError) as e:
     print(e)
     return invalidBill
   data=response.get_data()
   html=data.decode('utf-8')
   #read the html source into an lxml object
   root=lxml.html.fromstring(html)
   result_table=root.xpath('//table[@class="bills"]')
   try:
     result_table=result_table[0]
   except IndexError:
     print "\t[WARNING] Cannot find result table in html source for link " + href_link + ". Skipping."
     return invalidBill
   if len(result_table.getchildren()) == 9:
     theBill.islaw=False
   elif len(result_table.getchildren()) == 13:
     theBill.islaw=True
   else:
     print "\t[WARNING] HTML table for bill " + href_link + " does not contain 9 or 13 rows. Skipping."
     return invalidBill
   #1. Name of the bill
   row=result_table.getchildren()[0].getchildren()
   reference="Име на законопроекта"
   reference=reference.decode('utf-8')
   if row[0].text_content() != reference:
     print "\t[WARNING] Unexpected " + reference + " row " + row[0].text_content() + " for bill" + href_link +". Skipping."
     #return invalidBill
   title=row[1].getchildren()[0].text_content()
   if title != referenceTitle:
     print "\t[WARNING] Unexpected " + reference + " row " + row[0].text_content() + " for bill" + href_link +". Skipping."
     #return invalidBill
   theBill.bill_name=title.encode('utf-8')
   #2. Signature 
   row=result_table.getchildren()[1].getchildren()
   reference="Сигнатура"
   reference=reference.decode('utf-8')
   if row[0].text_content() != reference:
     print "\t[WARNING] Unexpected " + reference + " row " + row[0].text_content() + " for bill" + href_link +". Skipping."
     #return invalidBill
   theBill.signature=row[1].text_content()
   #3. Date
   row=result_table.getchildren()[2].getchildren()
   reference="Дата на постъпване"
   reference=reference.decode('utf-8')
   if row[0].text_content() != reference:
     print "\t[WARNING] Unexpected " + reference + " row " + row[0].text_content() + " for bill" + href_link +". Skipping."
     #return invalidBill
   theBill.date=dt.datetime.strptime(row[1].text_content(),"%d/%m/%Y")
   #4. Session
   row=result_table.getchildren()[3].getchildren()
   reference="Сесия"
   reference=reference.decode('utf-8')
   if row[0].text_content() != reference:
     print "\t[WARNING] Unexpected " + reference + " row " + row[0].text_content() + " for bill" + href_link +". Skipping."
     #return invalidBill
   theBill.session=row[1].text_content().encode('utf-8')
   #5 Bill text
   row=result_table.getchildren()[4].getchildren()
   reference="Текст на законопроекта"
   reference=reference.decode('utf-8')
   if row[0].text_content() != reference:
     print "\t[WARNING] Unexpected " + reference + " row " + row[0].text_content() + " for bill" + href_link +". Skipping."
     #return invalidBill
   for p in row[1].getchildren():
     if p.tag=='a':
       file_link=p.values()[0]
       file_name=href_link[1:].replace("/","-")+p.values()[0].split("bills")[1].replace("/","-")
       f=urllib.urlretrieve(file_link,filename="text/"+file_name)
       theBill.text.append(file_name.encode('utf-8'))
   #6 Issuers
   row=result_table.getchildren()[5].getchildren()
   reference="Вносители"
   reference=reference.decode('utf-8')
   if row[0].text_content() != reference:
     print "\t[WARNING] Unexpected " + reference + " row " + row[0].text_content() + " for bill" + href_link +". Skipping."
     #return invalidBill
   for li in row[1].getchildren()[0].getchildren():
     for lii in li.getchildren():
       lii_name=lii.text_content()
       lii_link=lii.values()[0]
       #example: getMp('Министерски съвет','http://www.government.bg/')
       theBill.issuers.append(getMp(lii_name,lii_link))
   #7 Comissions
   row=result_table.getchildren()[6].getchildren()
   reference="Разпределение по комисии"
   reference=reference.decode('utf-8')
   if row[0].text_content() != reference:
     print "\t[WARNING] Unexpected " + reference + " row " + row[0].text_content() + " for bill" + href_link +". Skipping."
     #return invalidBill
   for c in row[1].getchildren()[0].getchildren():
     theBill.commission.append(c.text_content().encode('utf-8'))
   #8 
   row=result_table.getchildren()[7].getchildren()
   reference="Доклади от комисии"
   reference=reference.decode('utf-8')
   if row[0].text_content() != reference:
     print "\t[WARNING] Unexpected " + reference + " row  " + row[0].text_content() + " for bill" + href_link +". Skipping."
     #return invalidBill
   
   for c in row[1].getchildren()[0].getchildren():
      for li in c.getchildren():
	text=getComissionText(BASE_LINK+li.values()[0])
	theBill.text.append(text.encode('utf-8'))
   #9 Chronology
   row=result_table.getchildren()[8].getchildren()
   reference="Хронология"
   reference=reference.decode('utf-8')
   if row[0].text_content() != reference:
     print "\t[WARNING] Unexpected "+reference+" row " + row[0].text_content() + " for bill" + href_link +". Skipping."
     #return invalidBill	
   for ul in row[1].getchildren():
     if len(ul)>0:
       for li in ul.getchildren():
         text=li.text_content()
         text_splitted=text.split("-")
         if len(text_splitted) !=2:
	   print "\t[WARNING] Strange chronology entry " + text + " for bill " + href_link + ". Skipping."
	   return invalidBill
         theBill.chronology[text_splitted[1].rstrip().encode('utf-8')] = dt.datetime.strptime(text_splitted[0].rstrip(),'%d/%m/%Y')
   if not theBill.islaw:
     return theBill
   #10 Status (only for bills that passed as laws)
   row=result_table.getchildren()[9].getchildren()
   reference="Статус"
   reference=reference.decode('utf-8')
   if row[0].text_content() != reference:
     print "\t[WARNING] Unexpected "+reference+" row " + row[0].text_content() + " for bill" + href_link +". Skipping."
     #return invalidBill
   theBill.status=row[1].text_content().encode('utf-8')
   #11 Date passed (only for bills that passed as laws)
   row=result_table.getchildren()[10].getchildren()
   reference="Дата на приемане"
   reference=reference.decode('utf-8')
   if row[0].text_content() != reference:
     print "\t[WARNING] Unexpected "+reference+" row " + row[0].text_content() + " for bill" + href_link +". Skipping."
     #return invalidBill
   theBill.date_passed=dt.datetime.strptime(row[1].text_content(),'%d/%m/%Y')
   #12 When published (only for bills that passed as laws) 
   row=result_table.getchildren()[11].getchildren()
   reference="Обнародван в ДВ"
   reference=reference.decode('utf-8')
   if row[0].text_content() != reference:
     print "\t[WARNING] Unexpected "+reference+" row " + row[0].text_content() + " for bill" + href_link +". Skipping."
     #return invalidBill
   theBill.when_published=row[1].text_content().encode('utf-8')
   #13 Final text of the law (Финален текст на закона) is skipped
   return theBill
       
if __name__ == "__main__":   
   #create the time intervals
   startYear=2001
   endYear=2014
   startMonth=7
   endMonth=12
   timeIntervals=[]
   for year in range(startYear,endYear+1):
     for month in range(startMonth,endMonth+1):
       timeIntervals.append(str(year)+"-"+str(month))
     startMonth=1
   ###
   allBills=[]
   timeCounter=0
   billCounter=0
   #check if progress file for this project exists
   if isfile("bills.progress"):
     try:
	allBills=pickle.load(open("billsData.pickled",'r'))
     except (IOError) as e:
       print e
     with open("bills.progress","r") as of:
       temp=of.readline()
       timeCounter=int(temp.split('\t')[0])
       billCounter=int(temp.split('\t')[1])
   ##   
   for bill in range(timeCounter,len(timeIntervals)):
     link=BASE_LINK+"/bg/bills/period/"+timeIntervals[bill]
     print "[INFO] "+link
     try:
       response=br.open(link)
     except (mechanize.HTTPError, mechanize.URLError) as e:
       print(e)
       continue
     print "\t[INFO] retrieved html source" 
     data=response.get_data()
     html=data.decode('utf-8')
     #read the html source into an lxml object
     root=lxml.html.fromstring(html)
     hrefs=root.xpath('//div[@id="monthview"]/ul')
     
     if len(hrefs) != 1:
       print "\t[WARNING] monthview div not found for " + link
       continue
     entries=hrefs[0].getchildren()
     if len(entries) == 0:
       print "\t[INFO] monthview div exists but has no children for " + link
       continue
     for b in range(billCounter,len(entries)):
       with open("bills.progress","w") as oo:
          print >> oo, str(bill) + '\t' + str(b)
       bb=entries[b].getchildren()
       if len(bb) != 1:
	 print "\t[INFO] Table element has more than one child. Taking first child"
       bb=entries[b][0]
       href=bb.keys()[0]
       href_link=bb.values()[0]
       if href != "href" or href_link.find("/bg/bills/ID/")!=0:
	 print "\t[WARNING] Strange bill href "+href_link + ". Skipping."
	 continue
       href_link_splitted=href_link.split("/bg/bills/ID/")
       try:
	 billID=int(href_link_splitted[1])
       except ValueError:
	 print "\t[INFO] Bill id not an integer for " + href_link
       print "\t[INFO] Bill " + href_link
       newBill = getNewBill(href_link,bb.text_content(),billID)
       #add only valid bills
       allBills.append(newBill)
       print "\t[INFO] Saving progress ..."
       #save the current status
       pickle.dump(allBills,open("billsData.pickled","wb"))
       