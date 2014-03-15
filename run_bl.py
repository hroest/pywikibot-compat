

import Levenshtein
# Python Levenshtein (apt-get install python-levenshtein) or
# http://pypi.python.org/pypi/python-Levenshtein/
import MySQLdb, spellcheck
import wikipedia as pywikibot
import pagegenerators
import temp, h_lib


################################################################################
# Create MySQL tables
################################################################################

"""
drop table hroest.all_words_20110514 ;
create table all_words_20110514 (
    article_id int,
    smallword varchar(255)
)
"""

reload( spellcheck )
db = MySQLdb.connect(read_default_file="~/.my.cnf.hroest")
cursor = db.cursor()
sp = spellcheck.Spellchecker(xmldump = 'xmldump/extend/dewiki-latest-pages-articles.xml.bz2')
gen = sp.de_wikidump.parse()
for page in gen:
    if not page.namespace == '0': continue
    prepare = [ [page.id, p.encode('utf8')] for p in sp.spellcheck_blacklist(page.text, {}, return_for_db=True)]
    tmp = cursor.executemany( """ insert into hroest.all_words_20110514
                   (article_id, smallword) values (%s,%s)""", prepare )

"""
drop table hroest.countedwords_20110514 ;
create table countedwords_20110514 as
select count(*)  as occurence, smallword as word from
all_words_20110514 group by smallword
"""


################################################################################
# Run
################################################################################
################################################################################
# here we check
# HERE WE START
###########################################################################
################################################################################
h_lib.assert_user_can_edit( u'Benutzer:HRoestTypo/BotTestPage', u'HRoestTypo')
sp = spellcheck.Spellchecker()
sp.readBlacklist(sp.blacklistfile, sp.blacklistencoding, sp.blackdic)
sp.readIgnoreFile(sp.ignorefile, 'utf8', sp.ignorePages)
db = MySQLdb.connect(read_default_file="~/.my.cnf.hroest", charset = "utf8", use_unicode = True)
db = MySQLdb.connect(read_default_file="~/.my.cnf.hroest")
cursor = db.cursor()
bb = temp.Blacklistchecker()

################################################################################
# Search and replace (single words or all possible)
################################################################################
wrongs = 'Universs'
corrects = 'Univers'

cursor.execute( """
select * from hroest.countedwords where word like '%s' order by occurence DESC;
""" % (wrongs+'%') )
allwrong = cursor.fetchall()

for wrong in allwrong:
    wrong = wrong[1]
    correct = wrong.replace( wrongs, corrects)
    if correct == wrong:
        correct = wrong.replace( wrongs[1:], corrects[1:])
    print wrong, correct
    wrong = wrong.decode('utf8')
    correct = correct.decode('utf8')
    # Do a single search and replace operation using mediawiki-search
    bb.searchNreplace(wrong, correct, replaceDerivatives)

#A single search and replace
wrong =   u'Dikographie'
correct =u'Diskographie'




################################################################################
# Search and replace previously found words
################################################################################
# errors: [[Lady Bird Johnson]] Familiy.jpg
# [[Ehe]] - [[Datei:Brauysegen im Bett.gif|miniatur|Wye reymont vnd melusina zuamen<!--sic!-->]]

skip = True
for k in replace:
    print k
    if k == u'bereit gestellt': skip = False
    if skip or k == u'bereit gestellt': continue
    wrong = k
    correct = replace[k]
    bb.searchNreplace(wrong, correct, replaceDerivatives)


import temp
reload(temp)
bb = temp.Blacklistchecker()
todo = {}
for k,v in rcount.iteritems():
    if v > 5 and not k == 'bereit gestellt':
        todo[k] = v
        print k,replace[k], v


for k,v in todo.iteritems():
        wrong = k
        correct = replace[k]
        wrong = wrong.decode('utf8')
        if correct.find(wrong) != -1: continue
        s = list(pagegenerators.SearchPageGenerator(wrong, namespaces='0'))
        pages = []
        for p in s: p.wrong = wrong; pages.append(p)
        wr = [p.wrong for p in pages]
        gen = pagegenerators.PreloadingGenerator(pages)
        bb.checkit(gen, wr, correct, replace, noall, rcount, sp)




################################################################################
# Find the most common words and search for missspells of those
################################################################################

cursor.execute(
"""
select * from hroest.countedwords where occurence > 1000
and length(word) > 6
order by occurence  DESC
""" )
misspell = cursor.fetchall()

myw = misspell[33][1]
myw = myw.decode('utf8')
#myw = 'Dezember'
#myw = 'August'
#myw = 'Mitglied'
#myw = u'schließlich'
#myw = 'Einwohner'
#myw = 'Beispiel'
#myw = 'insgesamt'
l = len(myw)
lcutoff = 0.8
print myw

# \xc2\xad is a soft hyphen that is sometimes used instaed of a space
#
# Search for all words that start with the same 3 chars
# then
sterm = myw[:3]
cursor.execute(
"""
select * from hroest.countedwords where word like '%s'
#and length(word) between %s and %s
and word not like '%s'
order by word
""" % (sterm.encode('utf8')+'%', l-2, l+2, myw.encode('utf8')+'%') )
similar = cursor.fetchall()
#original = [s for s in similar if s[1] == myw][0]
#original_count = original[0]
candidates = [s[1] for s in similar if
              Levenshtein.ratio(myw,s[1].decode('utf8')) > lcutoff and
              s[1] != myw #and s[0] *1.0 / original_count < 1e-3]
              and s[0] < 20 and not '\xc2\xad' in s[1]]
# Search for all words that start with the same char and end with the same 3 chars
sterm = myw[0] + '%' + myw[-3:]
cursor.execute(
"""
select * from hroest.countedwords where word like '%s'
#and length(word) between %s and %s
and word not like '%s'
order by word
""" % (sterm.encode('utf8')+'%', l-2, l+2, myw.encode('utf8')+'%') )
similar = cursor.fetchall()
#original = [s for s in similar if s[1] == myw][0]
#original_count = original[0]
candidates.extend(  [s[1] for s in similar if
              Levenshtein.ratio(myw,s[1].decode('utf8')) > lcutoff and
              s[1] != myw #and s[0] *1.0 / original_count < 1e-3]
              and s[0] < 20 and not '\xc2\xad' in s[1]] )
#get unique ones
candidates = list(set( candidates ) )
print len(candidates)

if True:
    correct = myw
    pages = []
    wrongwords = []
    for i, wrong in enumerate(candidates):
        #occ = wrong[0]
        #wrong = wrong[1]
        #if wrong != 'Dezcember': continue
        print i, wrong#, '(%s)' % occ
        wrongwords.append(wrong)
    #
    toignore = pywikibot.input('Ignore?')
    toignore = [int(t) for t in toignore.split(' ') if t != '']
    #
    for i, wrong in enumerate(candidates):
        wrong = wrong.decode('utf8')
        if correct.find(wrong) != -1: continue
        if i in toignore: continue
        s = list(pagegenerators.SearchPageGenerator(wrong, namespaces='0'))
        print wrong, len(list(s))
        if len(list(s)) == 100:
            s = list(pagegenerators.SearchPageGenerator("%s" % wrong, namespaces='0'))
            print "now we have ", len(s), " found"
            if len(list(s)) == 100: s = s[:15]
        for p in s: p.wrong = wrong; pages.append(p)

wr = [p.wrong for p in pages]
gen = pagegenerators.PreloadingGenerator(pages)
bb.checkit(gen, wr, correct, replace, noall, rcount, sp)




allws = [r for r in replace if replace[r] == myw ]
corrects = myw
for wrongs in allws:
    bb.searchDerivatives(wrongs, corrects, cursor, replaceDerivatives, wrongs)


import temp
reload(temp)
bb = temp.Blacklistchecker()

sum(rcount.values())

# store to wikipedia
if True:
    s = ''
    for k in sorted(replace.keys()):
        s += '* %s : %s\n' % (k, replace[k])
    mypage = pywikibot.Page(pywikibot.getSite(), 'User:HRoestTypo/replaced')
    mypage.put( s )
    s = ''
    for k in sorted(noall):
        s += '* %s \n' % (k)
    mypage = pywikibot.Page(pywikibot.getSite(), 'User:HRoestTypo/correct')
    mypage.put( s )
    s = ''
    for k in sorted(rcount.keys()):
        if rcount[k] > 0: s += '* %s : %s\n' % (k, rcount[k])
    mypage = pywikibot.Page(pywikibot.getSite(), 'User:HRoestTypo/replacCount')
    mypage.put( s )
    s = ''
    for k in sorted(replaceDerivatives.keys()):
        s += '* %s : %s\n' % (k, replaceDerivatives[k])
    mypage = pywikibot.Page(pywikibot.getSite(), 'User:HRoestTypo/replacedDerivatives')
    mypage.put( s )



# Load from wikipedia
if True:
    mypage = pywikibot.Page(pywikibot.getSite(), 'User:HRoestTypo/replaced')
    text = mypage.get()
    lines = text.split('* ')[1:]
    myreplace = {}
    for l in lines:
        spl =  l.split(' : ')
        myreplace[spl[0]] = spl[1].strip()
    mypage = pywikibot.Page(pywikibot.getSite(), 'User:HRoestTypo/correct')
    text = mypage.get()
    lines = text.split('* ')[1:]
    mycorrect = []
    for l in lines:
        mycorrect.append( l.strip() )
    mypage = pywikibot.Page(pywikibot.getSite(), 'User:HRoestTypo/replacCount')
    text = mypage.get()
    lines = text.split('* ')[1:]
    mycount = {}
    for l in lines:
        spl =  l.split(' : ')
        mycount[spl[0]] = int(spl[1].strip() )
    mypage = pywikibot.Page(pywikibot.getSite(), 'User:HRoestTypo/replacedDerivatives')
    text = mypage.get()
    lines = text.split('* ')[1:]
    myreplacedd = {}
    for l in lines:
        spl =  l.split(' : ')
        myreplacedd[spl[0]] = spl[1].strip()

replace = myreplace
noall = mycorrect
rcount = mycount
replaceDerivatives = myreplacedd


################################################################################
# use the (personal) blacklist created from permutations
################################################################################
cursor.execute('select * from hroest.blacklist_found')
a = cursor.fetchall()

ww = sp.spellcheck_blacklist( page.text, sp.blackdic)
self.prepare = []
for w in ww:
    self.prepare.append([page.title.encode('utf8'), page.id , w[2],
                    w[1].word, w[0], w[3], version])

cursor.executemany(
"INSERT INTO hroest.blacklist_found (%s)" % values +
    "VALUES (%s,%s,%s,%s,%s,%s,%s)", self.prepare)

######################################
#SPELLCHECK BLACKLIST / XML
######################################
#http://de.wikipedia.org/w/index.php?title=Volksentscheid&diff=61305581&oldid=61265643
import spellcheck, h_lib
h_lib.assert_user_can_edit( u'Benutzer:HRoestTypo/BotTestPage', u'HRoestTypo')
spellcheck.workonBlackXML(breakUntil='', batchNr=10000)


###################################
# Blacklist from the db
###################################

# TODO exclude everything after Literatur
# if and only if it is the latest header
# TODO exclude if line starts with *
sp.doNextBlackBatch_db(10000000, gen, db, '20101013')

# about 50% result in
donealready = 900
version = 20101013
pages = sp.get_blacklist_fromdb(db, donealready, version, 100)
next_done = max([p.dbid for p in pages])
sp.processWrongWordsInteractively( pages )



limit = 100
cursor = db.cursor()
values = """article_title, article_id, location, bigword_wrong,
        word_wrong, word_correct, version_used, id """
q = """ select %s from hroest.blacklist_found
               where word_correct like '%s'
               and version_used = %s
               order by id limit %s
               """ % (values, 'Univers%', version, limit)
cursor.execute(q)
lines = cursor.fetchall()
pages = sp._get_blacklist_fromdb(lines)

sp.processWrongWordsInteractively( pages )
