#!/usr/bin/python
# -*- coding: utf-8  -*-

import wikipedia as pywikibot
from xml.dom import minidom   #XML Parsing for API
import codecs
from datetime import datetime

def getReviewedPages(user_name, site = pywikibot.getSite() ):
    """Use API to get all reviewed pages for a user"""
    #http://de.wikipedia.org/w/api.php?action=query&list=logevents&lelimit=max&leuser=Firefox13&letype=review&format=xml
    #http://de.wikipedia.org/wiki/Spezial:Linkliste/Benutzer:Hannes_R%C3%B6st/Vorlage/Sichter
    nextStart = ''
    reviewedPages = []
    #
    predata = {
                'action'        : 'query',
                'format'        : 'xml',
                'list'          :  'logevents',
                'lelimit'       :  '500',
                'leuser'        :  user_name,
                'letype'        :  'review',
    }
    #address = wikipedia.getSite().protocol() + '://'
    #address += wikipedia.getSite().hostname()
    address = site.family.api_address( site.lang )
    #
    while True:
        #print('iteration %s' % nextStart)
        predata['lestart'] = nextStart
        response, data = site.postForm(address, predata=predata)
        dom = minidom.parseString(data.encode('utf8'))
        items = dom.getElementsByTagName('item')
        for node in items:
            thisAction = node.getAttribute('action')
            #es existieren: approve         Nachsichten
            #               approve-a       Automatisch
            #               approve-i       Initial
            #               approve-ia      Initial & Automatisch (neu erstellt)
            if thisAction == 'approve':
                revisions = node.getElementsByTagName('param')
                thisLogID = node.getAttribute('logid')
                thisPageID = node.getAttribute('pageid')
                thisTimestamp = node.getAttribute('timestamp')
                #firstchild = old revision
                #secondchild = previous (not reviewed) revision
                reviewedPages.append([thisPageID, thisLogID, revisions[0].firstChild.data, thisTimestamp])
        cont = dom.getElementsByTagName('query-continue')
        if not len(cont) == 0:
            nextStart = cont[0].getElementsByTagName('logevents')[0].getAttribute('lestart');
        else: break
    return reviewedPages

def postReviewedPagesandTable( user_name, site = pywikibot.getSite() ):
    output, rev = getReviewedTable( user_name, site )
    if output == -1: return
    f_revs = len( rev )
    flagPage = pywikibot.Page( site,
                      u'Benutzer:%s/Sichterbeiträge' % user_name )
    flagPage.put_async( str(f_revs), u'Update der Sichterbeiträge' )
    tablePage = pywikibot.Page( site,
                      u'Benutzer:%s/Sichtertabelle' % user_name )
    outstr = ''
    for o in output:
        outstr += o
    tablePage.put_async( outstr, 'Update der Sichtertabelle' )

def getNrReviewedPages(user_name):
    return len(getReviewedPages(user_name))

def getReviewedTable(user_name, site):

    rev = getReviewedPages(user_name, site)

    #user doesnt exist or something in that direction
    if len( rev ) == 0: return -1, []

    times =[]
    for tt in rev:
        times.append(parseISO8601(tt[3]))

    output = ["{| class=\"wikitable\"\n!Jahr\n!Monat\n!Sichtungen"]
    i = 0
    month_c = 0
    while i < len(times):
        #count at least the first review. All other than first are caught below
        count = 1
        while  i < len(times)-1 and (times[i].month == times[i+1].month):
            count += 1
            i += 1
        output.append("\n|-\n| %s\n| %s\n| %s" % (times[i].year, times[i].month, count) )
        i += 1
        month_c += 1

    output.append("\n|-\n| %s\n| %s\n| %s" % ("Average","/ Monat",
                                              len(rev)*1.0/month_c ) )
    output.append("\n|-\n| %s\n| %s\n| %s" % ("Total","-", len(rev) ) )
    output.append("\n|}")

    return output, rev

def writeReviewedTable(user_name, filename):
    output, rev = getReviewedTable( user_name )
    f = codecs.open(filename, 'w', encoding = "UTF8")
    f.writelines(output)

def parseISO8601(x):
    year1 = int(x[0:4])
    month1 = int(x[5:7])
    day1 = int(x[8:10])
    hour1 = int(x[11:13])
    minute1 = int(x[14:16])
    second1 = int(x[17:19])
    return datetime(year1, month1, day1, hour1, minute1, second1)

