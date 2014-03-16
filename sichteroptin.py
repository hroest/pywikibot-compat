#!/usr/bin/python
# -*- coding: utf-8  -*-

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
h_lib.assert_user_can_edit( 'Benutzer:HRoestBot/BotTestPage', 'HRoestBot')

#params
optinhashfile =  '/home/hroest/optinHash.py'

optin = 'Benutzer:HRoestBot/Nachsichten/SichterOptIn'
optinPage = wikipedia.Page(wikipedia.getSite(),optin)
text = optinPage.get()
names = text.split('\n')
names = [n for n in names if n != '']
for name in names:
    print name.encode('utf-8')
    ReviewBotLib.postReviewedPagesandTable( name, site )

#now do the optin-hash
query = """
select user_id, user_name from dewiki_p.user
where user_name in ('%s')
""" % "', '".join( names )

import MySQLdb
db = MySQLdb.connect(read_default_file="/home/hroest/.my.cnf")
c = db.cursor()
c.execute( query.encode('utf-8') )
lines = c.fetchall()
f = open( optinhashfile, 'w')
f.write( '# -*- coding: utf-8  -*-\n')
f.write( 'optinhash = {\n')
for l in lines:
    f.write( "%s : '%s',\n" % (l[0], l[1]) )

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
