#!/usr/bin/python
# -*- coding: utf-8  -*-

# This code parses the page Benutzer:HRoestBot/Nachsichten/SichterOptIn and
# gets a list of all people that would like to get an update of their revision

#params
optinhashfile = '/home/hroest/optinHash.py'
optin = 'Benutzer:HRoestBot/Nachsichten/SichterOptIn'
switch_bot_page = u'Benutzer:HRoestBot/Sichterbeiträge' 

import wikipedia
import ReviewBotLib
site = wikipedia.getSite()
site.completely_quiet = True

def assert_user_can_edit( testpage, botname):
    import random
    tPage = wikipedia.Page(wikipedia.getSite(),testpage)
    result = tPage.put( 'myTest %d' % (1000* random.random() ) )
    latest = tPage.getVersionHistory()[0]
    assert result[2]['result'] == 'Success'
    assert latest[0] == result[2]['newrevid']
    assert latest[2] == botname

#assert we can edit
assert_user_can_edit( 'Benutzer:HRoestBot/BotTestPage', 'HRoestBot')

# get new data from optin page and update the optinHash.py
optinPage = wikipedia.Page(wikipedia.getSite(),optin)
text = optinPage.get()
names = text.split('\n')
names = [n.strip() for n in names if n != '']

switch_sichter = " {{#switch: {{{1}}}" 
for name in names:
    print name.encode('utf-8')
    nr_revs, outtable = ReviewBotLib.postReviewedPagesandTable( name, site )
    if nr_revs == -1: 
        continue

    switch_sichter += " | " + name + " = " + str(nr_revs) + "\n"

switch_sichter += " }}"
botpage = wikipedia.Page( site, switch_bot_page)
botpage.put_async( switch_sichter,  u'Update der Sichterbeiträge' )

#now do the optin-hash
sanatized_names = [n.replace("'", "\\'") for n in names]
query = """
select user_id, user_name from dewiki_p.user
where user_name in ('%s')
""" % "', '".join( sanatized_names )

import MySQLdb
db = MySQLdb.connect(read_default_file="/home/hroest/.my.cnf")
c = db.cursor()
c.execute( query.encode('utf-8') )
lines = c.fetchall()
f = open( optinhashfile, 'w')
f.write( '# -*- coding: utf-8  -*-\n')
f.write( 'optinhash = {\n')
for l in lines:
    sanitized_name = l[1].replace("'", "\\'")
    f.write( "%s : '%s',\n" % (l[0], sanitized_name ))

f.write( "495664 : 'Bot',")
f.write( "560646 : 'Bot',")
f.write( "'dummy' : -1}")
f.close()

#typo

editcount = 'Benutzer:HRoestTypo/editcount'
editcountpage = wikipedia.Page(wikipedia.getSite(),editcount)

c.execute( "select user_editcount from dewiki_p.user where user_name='HRoestTypo';")
count = c.fetchall()[0][0]
editcountpage.put( str(count ) )
