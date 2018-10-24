#!/usr/bin/python3
#I'm putting the whole program to a single file to keep the script-program behaviour
#without any program specific installations

import csv
from cycler import cycler
import argparse
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np

####### Config Area #########
## adapt to your analysis
#the input file of bookings. CVS exported from the banking website
INPUT_FILE="NoFile.CSV"
#the group-definitions with filter strings
FILTER_FILE="GroupFilter.CSV"

########### end config area

myBookings=None
myFilter=None
myDateWindows=None
mySpendingsDetail=None
mySpendingSum=None

class DateWindow:
    def __init__(self):
        self.startDate=datetime.now()
        self.endDate=datetime.now()
        self.name=""

    def isPartOf(self, bookRow):
        checkDate=bookRow["Day"]
        isIn=(checkDate>=self.startDate) and (checkDate<self.endDate)
        return isIn

class DateWindowCreator:
        def __init__(self):
            return

        def createDateWindows(self, bookingRows):
            #do not assume the rows are sorted by date
            #first find the earliest date
            #the last date is just put to 'today'. Later bookings are highly unlikely ;-)
            #the find all dates of bookings belonging to 'LOHN'
            #sort these dates
            #assing the names to the windows

            #So, find the smallest date and the 'Lohn' Dates
            edgeDates=[]
            smallDate=datetime.now()
            strSalary="Lohn"
            for book in bookingRows:
                if book["Day"]<smallDate:
                    smallDate=book["Day"]

                if ((book["Group"]=="Einkommen") and (strSalary in book["Reason"])):
                    edgeDates.append(book["Day"])
            edgeDates.append(smallDate)
            edgeDates.append(datetime.now())

            edgeDates.sort()
            self.DateWindows=[]
            for idx in range(0,len(edgeDates)-1):
                newDateWindow=DateWindow()
                newDateWindow.startDate=edgeDates[idx]
                newDateWindow.endDate=edgeDates[idx+1]
                nameDate=newDateWindow.startDate
                newDateWindow.name=nameDate.strftime("%Y-%m-%d")
                self.DateWindows.append(newDateWindow)
            return self.DateWindows

class Filter:
    def __init__(self):
        self.name = ""
        self.match = []
        return

    def isPartOf(self, bookRow):
        inIn=False
        check1=bookRow["Reason"].lower()
        check2=bookRow["Receiver"].lower()
        check3=bookRow["Buchungstext"].lower()
        for filter in self.match:
            isIn=(filter.lower() in check1) or (filter.lower() in check2) or (filter.lower() in check3)
            if isIn: break;

        return isIn

class FilterImporter:
    def __init__(self):
        return

    def readFilter(self, filename):
        filterList=[]

        with open(filename, 'r', encoding='UTF-8') as csvfile:
            dialect = csv.Sniffer().sniff(csvfile.read(1024))
            csvfile.seek(0)
            reader = csv.reader(csvfile, delimiter=";", quotechar='\"')
            for row in reader:
                if (len(row) > 1):
                    newFilter=Filter()
                    newFilter.name=row[0]
                    for idx in range(1,len(row)):
                        newFilter.match.append(row[idx])
                    filterList.append(newFilter)
        return filterList

class CSVImporter:
    def __init__(self):
        return

    def readData(self, filename):
        with open(filename, 'r', encoding='iso-8859-1') as csvfile:
            dialect = csv.Sniffer().sniff(csvfile.read(1024))
            csvfile.seek(0)
            reader = csv.DictReader(csvfile, delimiter=";", quotechar='\"')

            dict_list=[]

            for row in reader:
                buchtext=row['Buchungstext']
                zweck=row['Verwendungszweck']
                buchtag=datetime.strptime(row['Buchungstag'], '%d.%m.%y')
                beguenst=row['Beguenstigter/Zahlungspflichtiger']
                wert=float((row['Betrag'].replace(',','.')))
                newrow={"Value":wert, "Day":buchtag, "Buchungstext":buchtext, "Receiver":beguenst, "Reason":zweck, "Group":"NOGROUP", "DateWindow":"NOWINDOW"}
                dict_list.append(newrow)
        return dict_list

class SpendingTable:
    def __init__(self):
        self.detailTable={}
        return

    def createTable(self, bookings, filter, windows):
        for win in windows:
            self.detailTable[win.name]={}
            self.detailTable[win.name]["NOGROUP"]=[]
            for fil in filter:
                self.detailTable[win.name][fil.name]=[]

        for book in bookings:
            self.detailTable[book["DateWindow"]][book["Group"]].append(book)

        return self.detailTable

def assignGroups(bookings, filter):
    for booking in bookings:
        for filt in filter:
            if filt.isPartOf(booking):
                booking["Group"]=filt.name
                break

def assignDateWindows(bookings, dateWindows):
    for booking in bookings:
        for win in dateWindows:
            if win.isPartOf(booking):
                booking["DateWindow"]=win.name
                break

def prepare(INPUT_FILE):
    myBookings = CSVImporter().readData(INPUT_FILE)
    myFilter = FilterImporter().readFilter(FILTER_FILE)
    assignGroups(myBookings, myFilter)
    myDateWindows = DateWindowCreator().createDateWindows(myBookings)
    assignDateWindows(myBookings, myDateWindows)
    spendings = SpendingTable()
    mySpendingsDetail = spendings.createTable(myBookings, myFilter, myDateWindows)
    return myBookings, myFilter, myDateWindows, mySpendingsDetail

def createArgumentParser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="input cvs file")
    parser.add_argument("-lg", "--list-groups", help="lists all available booking groups", action="store_true")
    parser.add_argument("-ld", "--list-dates", help="lists all available date-windows", action="store_true")
    parser.add_argument("-g","--groups", help="Set the booking-groups for the analysis", nargs='+', metavar=('GROUP'))
    parser.add_argument("-d", "--date-window", help="selects the date-window to analyse. 'END' must be larger or equal to 'START', Just the first 'END' is valid. Optional others are discarded.", nargs='+', metavar=('START','END'))
    parser.add_argument("-s", "--sum", help="prints the sum of the selected group and/or date window", action="store_true")
    parser.add_argument("-c","--chart", help="prints a graph of the sums. Only works for sums.", action="store_true")

    parser.add_argument("-cvs", "--export-cvs", help="exports the query to the given cvs file")

    return parser

def printGroups(mySpendingsDetail):
    print("Available booking groups to select from")
    test = list(mySpendingsDetail.keys())
    groupTitles = list(mySpendingsDetail[test[0]].keys())
    groupTitles.sort()
    for entry in groupTitles:
        print("* ",entry)
    print()

def printDates(mySpendingsDetail):
    print("Available date-windows to select from")
    dateTitles = list(mySpendingsDetail.keys())
    dateTitles.sort()
    for entry in dateTitles:
        print("* ", entry)

def query(dates, groups, detailTab):
    result=[]
    queryTab=None

    queryTab=detailTab

    if (dates!=None):
        for date in dates:
            if (groups==None):
                for key in queryTab[date].keys():
                    result.append(queryTab[date][key])
            else:
                for group in groups:
                    result.append(queryTab[date][group])
    else:
        if (groups != None):
            tmpResult=[]
            for group in groups:
                for key in queryTab.keys():
                    tmpResult.append(queryTab[key][group])
            result=tmpResult

    return result

def getDistinctDateTime(query):
    distinct=[]
    for groups in query:
        for details in groups:
            distinct.append(details["DateWindow"])

    distinct=set(distinct)
    distinct=sorted(distinct)
    return distinct

def printQuery(sum, filterinfo, query):
    dateName="N/A"
    dateTimes=getDistinctDateTime(query)
    allGroups=["NOGROUP"]
    for filter in filterinfo:
        allGroups.append(filter.name)

    for datetime in dateTimes:
        dateIncome=0.0
        dateSpend=0.0
        print("****** ",datetime, " **********" )
        for groupname in allGroups:
            groupList=[]
            for entry in query:
                for line in entry:
                    if (line["DateWindow"]==datetime and line["Group"]==groupname):
                        groupList.append(line)
            if len(groupList)>0 :
                print("######## ", groupname, "#########")
                grpSum=0.0
                #groupList=groupList.sort(axis=0)
                for prnt in groupList:
                    if (sum==False):
                        print("...... ",prnt["Day"], "   ", prnt["Value"], "   ",prnt["Reason"]," --- ", prnt["Receiver"])
                    else:
                        grpSum+=prnt["Value"]
                if (sum==True):
                    print("----> Summe: %6.2f€" %grpSum)
                    if(grpSum>0):
                        dateIncome+=grpSum
                    else:
                        dateSpend+=grpSum
        if (sum==True):
            print()
            print("-------------------------")
            print("Income  : %6.2f€" %dateIncome)
            print("Spending: %6.2f€" %dateSpend)
            print("Diff    : %6.2f€" %(dateIncome+dateSpend))
            print("-------------------------")

def calcSum(dateWindow, group, mySpendingsDetail):
    entries=mySpendingsDetail[dateWindow][group]
    grpSum=0.0
    if len(entries) > 0:
        grpSum = 0.0
        for entry in entries:
            grpSum += entry["Value"]
    return grpSum


def createSummaryTable(dateWindows, groups, mySpendingsDetail, filterinfo):
    summaryTable=[]
    summaryRow=[""]
    IncomeRow=["Income"]
    SpendRow=["Spendings"]
    DiffRow=["Savings"]

    if (dateWindows==None):
        dateWindows = getDistinctDateTime(mySpendingsDetail)
    for date in dateWindows:
        summaryRow.append(date)
        IncomeRow.append(0.0)
        SpendRow.append(0.0)
        DiffRow.append(0.0)
    summaryTable.append(summaryRow)

    if (groups==None):
        allGroups = ["NOGROUP"]
        for filter in filterinfo:
            allGroups.append(filter.name)
        groups=allGroups
    for group in groups:
        summaryRow=[group]
        idx=1
        for date in dateWindows:
            grpsum=calcSum(date,group, mySpendingsDetail)
            summaryRow.append(grpsum)
            if (grpsum>0.0):
                IncomeRow[idx]+=grpsum
            else:
                SpendRow[idx]+=grpsum
            idx+=1

        summaryTable.append(summaryRow)

    for idx in range(0, len(dateWindows)):
        DiffRow[idx+1]=IncomeRow[idx+1]+SpendRow[idx+1]

    summaryTable.append(IncomeRow)
    summaryTable.append(SpendRow)
    summaryTable.append(DiffRow)

    return summaryTable



def main():
    parser = createArgumentParser()
    args = parser.parse_args()
    if (args.input!=None):
        INPUT_FILE=args.input

    myBookings, myFilter, myDateWindows, mySpendingsDetail = prepare(INPUT_FILE) #read and parse all input data and prepare the tables



    dateWindows=None
    groups=None

    if (args.list_groups):
        printGroups(mySpendingsDetail)
    if (args.list_dates):
        printDates(mySpendingsDetail)

    if (args.date_window!=None):
        if (len(args.date_window)>0):
            dateWindowStart=args.date_window[0]
            dateTitles = list(mySpendingsDetail.keys())
            dateTitles.sort()
            dateWindows=[dateTitles[0]]
            for aktdate in dateTitles:
                if (aktdate>dateWindowStart):
                    break
                dateWindows[0]=aktdate
            if(len(args.date_window)>1):
                dateWindowEnd=args.date_window[1]
                if(dateWindowEnd>=dateWindows[0]):
                    for aktdate in dateTitles:
                        if (aktdate>dateWindows[0]):
                            dateWindows.append(aktdate)
                            if(aktdate>dateWindowEnd):
                                break

    if (args.groups!=None):
        if (len(args.groups)>0):
            groups=args.groups

    if (args.sum):
        sumTable=createSummaryTable(dateWindows,groups,mySpendingsDetail, myFilter)
        headline=sumTable[0]
        incomeline=sumTable[-3]
        spendingline=sumTable[-2]
        diffline=sumTable[-1]
        styles=plt.style.available
        plt.style.use('ggplot')

        if (args.chart):
            bars=[]
            groupnames=[]
            ind=np.arange(len(dateWindows))
            testSum = 0.0

            aktbottom=np.zeros(len(dateWindows))
            for line in sumTable[1:-3]:
                absline=[]
                if (line[0]!="Einkommen"):
                    groupnames.append(line[0])
                    for val in line[1:]:
                        absline.append(round(abs(val)))
                    bar=plt.bar(ind, absline, 0.35, bottom=aktbottom)
                    aktbottom=np.sum([aktbottom, absline], axis=0)
                    bars.append(bar)

            plt.legend(bars, groupnames, loc='upper center', bbox_to_anchor=(0.5, 1.1), ncol=6)
            plt.plot(dateWindows, incomeline[1:],'g')
            sline=[]
            for val in spendingline[1:]:
                sline.append(abs(val))
            plt.plot(dateWindows, sline,'r')
            #plt.plot(dateWindows, diffline[1:],'b')
            plt.ylabel('€')
            plt.grid(True, which='both')
            plt.xticks(ind, dateWindows)
            plt.show()


        else:
            for row in headline:
                print("%18s |" %row, end="")
            print()
            print((("-" * 19)+"+") * len(headline))
            for idx in range(1, len(sumTable)):
                aktRow=sumTable[idx]
                if(aktRow[0]=="Income"):
                    print("="*20*len(aktRow))
                print("%18s |" %aktRow[0], end="")
                for idx2 in range(1, len(aktRow)):
                    print("%18.2f |" %aktRow[idx2], end="")
                print()
    else :
        result = query(dateWindows, groups, mySpendingsDetail)
        printQuery(args.sum, myFilter, result)

    exit()


if __name__ == '__main__':
    main()






