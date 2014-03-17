#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
This bot spellchecks Wikipedia pages using a list of bad words. 
"""

#
# (C) Andre Engels, 2005
# (C) Pywikipedia bot team, 2006-2011
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import re, sys, time
import string, codecs
import hunspell, webbrowser
import xmlreader
import pickle
import wikipedia as pywikibot
import pagegenerators, catlib

from spellcheck import SpecialTerm, distance, getalternatives, cap, uncap
from spellcheck import removeHTML

from spellcheck_hunspell import Word
from spellcheck_hunspell import abstract_Spellchecker
from spellcheck_hunspell import CallbackObject

from InteractiveWordReplacer import InteractiveWordReplacer
from InteractiveWordReplacer import BlacklistSpellchecker

correct_html_codes = False

def readBlacklist(filename, blackdic, encoding="utf8"):
    f = codecs.open(filename, 'r', encoding = encoding)
    for line in f.readlines():
        # remove trailing newlines and carriage returns
        try:
            while line[-1] in ['\n', '\r']:
                line = line[:-1]
        except IndexError:
            pass
        #skip empty lines
        if line != '':
            line = line.split(';')
            blackdic[ line[0].lower() ] = line[1]

def writeBlacklist(filename, encoding, blackdic):
    f = codecs.open(filename, 'w', encoding = encoding)
    for key in sorted(blackdic.keys()):
        f.write('%s;%s\n' % (key, blackdic[key]))
    f.close()


class Spellchecker(abstract_Spellchecker):
    """ Blacklist based spellchecker

    This spellchecker reads in a "blacklist" of words that are commonly spelled
    wrong and checks a gien text against this list.

    Possible usage
    >>> sp = spellcheck.Spellchecker()
    >>> readBlacklist(sp.blacklistfile, sp.blackdic)
    >>> result = sp.spellcheck_blacklist(text, {'Deuschland' : 'wrong'})
    """

    def __init__(self, xmldump=None):
        if xmldump is None:
            xmldump = 'xmldump/extend/dewiki-latest-pages-articles.xml.bz2'
        else:
          self.de_wikidump = xmlreader.XmlDump(xmldump)
        self.blacklistfile = 'blacklist.dic'
        self.blacklistencoding = 'utf8'
        self.ignorefile = 'ignorePages.txt'
        self.ignorefile_perpage = 'ignorePerPages.txt'
        self.ignorePages = []
        self.ignorePerPages = {}
        self.unknown = []

        self.nosugg = []
        self.encounterOften = []
        self.suggestions_dic = {}
        self.replaceBy = {}
        self.blackdic = {}
        self.Callbacks = []
        self.gen = []

    def writeIgnoreFile(self):
        """
        self.writeIgnoreFile(self.ignorefile, 'utf8', self.ignorePages)
        import pickle
        f = open(self.ignorefile_perpage,'w'); pickle.dump( self.ignorePerPages, f); f.close()
        """
        filename = self.ignorefile
        encoding = 'utf8'
        self.ignorePages
        f = codecs.open(filename, 'w', encoding = encoding)
        for entry in sorted(self.ignorePages):
            f.write('%s\n' % entry )

        f.close()

        f = codecs.open(self.ignorefile_perpage, 'w', encoding = encoding)
        f.write('mydumpeddic = {\n' )
        for k in sorted(self.ignorePerPages):
            f.write('%s : %s,\n' % (k,self.ignorePerPages[k]) )

        f.write('9:9}\n' )
        f.close()

    def readIgnoreFile(self, filename, encoding, ignore):
        f = codecs.open(filename, 'r', encoding = encoding)
        for line in f.readlines():
            # remove trailing newlines and carriage returns
            line = line.strip()
            #skip empty lines
            if line != '':
                ignore.append( line )

    #
    # Call workonBlackXML on the top
    #   while True:
    #    =>  calls doNextBlackBatch
    #          --> calls spellcheck_blacklist
    #    =>  calls the interactive word replaces
    #
    def workonBlackXML(self, breakUntil = '', batchNr = 3000, doNoninteractive=False):
        import pickle
        readBlacklist(self.blacklistfile, self.blackdic, encoding = self.blacklistencoding)
        self.readIgnoreFile(self.ignorefile, self.blacklistencoding, self.ignorePages)
        f = open( self.ignorefile_perpage); self.ignorePerPages = pickle.load(f)

        wr = InteractiveWordReplacer()

        generator = append(self.de_wikidump.parse())

        print("Blacklist successfully loaded")
        i = 0
        if not breakUntil == '':
            for page in generator:
                if page.title == breakUntil: break;
                i += 1
                if i % 100 == 0:
                    sys.stdout.flush()
                    sys.stdout.write("\rSearched pages: %s" % i)

        print("\nStarting to work on batches")
        if doNoninteractive:
            nrpages = 10000
            #here we all of them, loop until the pages done is not 10k any more
            while nrpages == 10000:
                res, nrpages = self.doNextBlackBatch( nrpages, generator )
            import pickle
            f = open( 'spellcheck_whole.dump', 'w')
            pickle.dump(res, f)
            f.close()
            return

        #f = open( 'spellcheck_whole.dump'); test = pickle.load(f)

        while True:
            wrongWords, nrpages = self.doNextBlackBatch(batchNr, generator)
            print('Found %s wrong words.' % len(wrongWords))
            wr.processWrongWordsInteractively( wrongWords )
            choice = pywikibot.inputChoice('Load next batch?',
                   ['Yes', 'yes', 'No'], ['y', '\\', 'n'])
            if choice == 'n': break

        errors = False
        doneSaving = True
        for call in self.Callbacks:
            try:
                if not call.error is None:
                    print('could not save page %s because\n:%s' % (call.page,
                           call.error)); errors = True
            except AttributeError:
                print('not done yet with saving')
                doneSaving = False

        if not errors and doneSaving:
            print('saved all pages')
            self.Callbacks = []

    def doNextBlackBatch(self, batchNr, gen, offline=False):
        """ We go through the whole batch and check the content
        at least we have a nice progress bar for the user
        """
        i = 0
        wrongWords = []
        p = progress.ProgressMeter(total=batchNr, unit='pages')
        for page in gen:
            if not page.namespace == '0': continue
            ww = self.spellcheck_blacklist( page.text, self.blackdic)
            if not len(ww) == 0: wrongWords.append([page, ww])
            i += 1
            p.update(1)
            if i > batchNr: break

        return wrongWords, i

    def spellcheck_blacklist(self, text, blackdic, return_for_db=False):
        """ Checks a single text against the words in the blacklist and returns
        a list of wrong words.

        Called by doNextBlackBatch or doNextBlackBatch_db or doBlacklistNoninteractively
        """
        if correct_html_codes:
            text = removeHTML(text)

        loc = 0 # the current location in the text we parse
        old_loc = 0
        curr_r = 0
        ranges = self.forbiddenRanges(text)
        ranges = sorted(ranges)
        wrongWords = []
        prepare = []
        self.blackdic = blackdic
        while True:
            #added "/" to first since sometimes // is in the text
            #added "/" to second since in german some words are compositions
            wordsearch = re.compile(r'([\s\=\<\>\_/-]*)([^\s\=\<\>\_/\-]+)')
            #wordsearch = re.compile(r'([\s\=\<\>\_]*)([^\s\=\<\>\_/\-]+)') #old one
            match = wordsearch.search(text,loc)
            LocAdd = 0

            if not match:
                # No more words on this page
                break

            # Check if we are in forbidden range
            curr_r, loc, in_nontext = self.check_in_ranges(ranges, 
                                       match.start(), match.end(), curr_r, loc)
            if in_nontext: 
                continue

            # Split the words up at special places like &nbsp; or a dash
            spl = re.split('&nbsp;', match.group(2))
            if len(spl) > 1: 
                LocAdd = 5
            elif len(spl) == 1:
                spl = re.split(u'–', spl[0])

            ww = spl[0]
            LocAdd += len(ww) + 1
            bigword = Word(ww)
            smallword = bigword.derive()

            # We advance the location by the characters skipped
            loc += len(match.group(1))
            done = False

            # if we have a <nowiki></nowiki> break before, we dont want to interpret
            if text[loc-17:loc] == '<nowiki></nowiki>':
                done = True
            # if we have a closing wikilink "]]" before, we dont want to interpret
            if text[loc-2:loc] == ']]':
                done = True

            # try to find out whether its an abbreviation and has a '.' without capitalization
            if loc+len(ww)+5 < len(text) and \
               text[loc+len(ww)-1] == '.' and \
               text[loc+len(ww)+1].islower() and \
               not text[loc+len(ww):loc+len(ww)+5] == '<ref>':
                done = True

            # words that end with ' or -
            if loc+len(ww) < len(text) and text[loc+len(ww)] == '-':
                done = True

            #exclude words that have uppercase letters in the middle
            for l in smallword[1:]:
                if l.isupper(): 
                    done=True;

            #exclude words that are smaller than 3 letters
            if len( smallword.lower() ) < 3: 
                done = True

            ###################################
            #use this code to insert into the database
            if return_for_db:
                if not done:
                    wrongWords.append(smallword)

            else:
                ###################################
                #here we check whether it is wrong
                if not done and smallword.lower() in self.blackdic \
                   and not smallword == '' and not smallword.isupper():

                    if not smallword == self.blackdic[smallword.lower()]:
                        wrongWords.append([smallword, bigword, loc, self.blackdic[smallword.lower()],
                            text[max(0, loc-100):min(loc+100, len(text))] ])

                # print "loc ", loc, " locadd ", LocAdd
            loc += LocAdd
        return wrongWords

    #
    # Database functions
    #   call doNextBlackBatch_db and then get_blacklist_fromdb instead of doNextBlackBatch_db
    #   then call interactive word replacement
    #
    def doNextBlackBatch_db(self, batchNr, gen, db, version):
        """
        This will go through a number of pages in the generator and compare
        their text to the blacklist. It will store the results in the db.

        Run get_blacklist_fromdb to get the pages back.
        """
        i = 0
        encoding = 'utf8'
        wrongWords = []
        cursor = db.cursor()
        p = progress.ProgressMeter(total=batchNr, unit='pages')
        values = """ article_title, article_id, location, bigword_wrong,
        word_wrong, word_correct, version_used """
        for page in gen:
            if not page.namespace == '0': continue
            ww = self.spellcheck_blacklist( page.text, self.blackdic)
            self.prepare = []
            for w in ww:
                self.prepare.append([page.title.encode(encoding), page.id , w[2],
                    w[1].word.encode(encoding), w[0].encode(encoding),
                    w[3].encode(encoding), version])
                #print self.prepare
            cursor.executemany(
            "INSERT INTO hroest.blacklist_found (%s)" % values +
                "VALUES (%s,%s,%s,%s,%s,%s,%s)", self.prepare)
            p.update(1)
            i += 1
            if batchNr > 0 and i > batchNr: break

    def get_blacklist_fromdb(self, db, donealready, version, limit=100):
        """This will return pages with words in the blacklist ready for
        the interactive word replacer.

        The pages have a dbid and words attached to them.

        WrongWord: word_wrong, location, bigword_wrong, word_correct
        """
        cursor = db.cursor()
        values = """article_title, article_id, location, bigword_wrong,
                word_wrong, word_correct, version_used, id """
        cursor.execute( """ select %s from hroest.blacklist_found
                       where id > %s and version_used = %s
                       order by id limit %s
                       """ % (values, donealready, version, limit) )
        lines = cursor.fetchall()
        return self._get_blacklist_fromdb(lines)

    def _get_blacklist_fromdb(self, lines):
        # First group by article id (all of the same article)
        grouping = {}
        for w in lines:
            myid = w[1]
            if grouping.has_key(myid): grouping[myid].append( w)
            else: grouping[myid] = [w]

        pages = []
        decoding = 'utf8'
        for k in grouping:
            page = pywikibot.Page(pywikibot.getSite(), w[0].decode(decoding) )
            page.words = []
            for w in grouping[k]:
                myword = WrongWord(wrong_word = w[4].decode(decoding),
                    location = w[2],
                    bigword = w[3].decode(decoding),
                    correctword = w[5].decode(decoding) )
                page.words.append( myword )
            page.dbid = w[7]
            pages.append( page )

        import pagegenerators
        gen = pagegenerators.PreloadingGenerator(pages)
        #for page in gen: pass
        return pages

    #
    # unused functions
    #
    def doBlacklistNoninteractively(self, gen):
        """This will run through ALL pages, check its spelling using a negative
        list them and return them.  Should be used in noninteractive mode where
        one wants to precompute all the pages on an XML file and then go
        through them later.
        """
        wrongWords = []
        i = 0
        import time
        start = time.time()
        for page in gen:
            if not page.namespace == '0': continue
            ww = self.spellcheck_blacklist( page.text, self.blackdic)
            if not len(ww) == 0: wrongWords.append([page, ww])
            if i % 10000 == 0:
                print i
                end = time.time()
                print "%.2f m = %s s" % ( (end- start) /(60.0) ,end- start   )
            i += 1
        return wrongWords, i

class WrongWord(Word):

    def __init__(self, wrong_word, location=-1, bigword='', correctword='',
                doReplace=False):
        self.location = location
        self.bigword = bigword
        self.correctword = correctword
        self.doReplace = doReplace

        Word.__init__(self, wrong_word)

def run_bot(allPages, sp, collect):
    collectedPages = []
    stillSkip  = False;
    firstPage = True
    start = time.time()
    seenAlready = {}
    wr = InteractiveWordReplacer()
    for page in allPages:
        if page.title() in seenAlready: 
            continue

        seenAlready[ page.title() ] = 0
        print page

        try:
            text = page.get()
        except pywikibot.NoPage:
            pywikibot.output(u"%s doesn't exist, skip!" % page.title())
            continue
        except pywikibot.IsRedirectPage:
            pywikibot.output(u"%s is a redirect, skip!" % page.title())
            continue

        orig_text = text

        ran = sp.forbiddenRanges(text)

        ww = sp.spellcheck_blacklist(text, sp.blackdic)
        # WrongWord: word_wrong, location, bigword_wrong, word_correct
        www = [WrongWord(w[0], w[2], w[1].word, w[3]) for w in ww]
        page.words = www
        collectedPages.append(page)
        if not collect:
            wr.processWrongWordsInteractively([page])

    print "==================================="
    print "Processing %s pages took %0.4fs" % (len(collectedPages), time.time() - start)
    if collect:
        wr.processWrongWordsInteractively(collectedPages)

def show_help():
    thishelp = u"""
Arguments for the Review Bot:

-start:            Start spellchecking with this page

-longpages:        Work on pages from Special:Longpages.

-blacklist:        Provide a list of wrong words (provide the wrong and the correct word per line separated by ;)

-collect:          Collects pages first before asking for feedback

-cat:              Recursively only work on pages of this category

    """
    print thishelp

def main():
    ###################################################################
    #                           MAIN                                  #
    ###################################################################
    title = []
    start = None
    newpages = False
    longpages = False
    rebuild = False
    checknames = True
    collectFirst = False
    category = None
    checklang = None
    blacklistfile = None

    sp = BlacklistSpellchecker()

    for arg in pywikibot.handleArgs():
        if arg.startswith("-start:"):
            start = arg[7:]
        elif arg.startswith("-cat:"):
            category = arg[5:]
        elif arg.startswith("-blacklist:"):
            blacklistfile = arg[11:]
        elif arg.startswith("-newpages"):
            newpages = True
        elif arg.startswith("-longpages"):
            longpages = True
        elif arg.startswith("-collect"):
            collectFirst = True
        elif arg.startswith("-html"):
            correct_html_codes = True
        elif arg.startswith('-h') or arg.startswith('--help'):
            pywikibot.showHelp()
            show_help()
            return
        else:
            title.append(arg)

        # This is a purely interactive bot, we therefore do not want to put-throttle
        pywikibot.put_throttle.setDelay(1)

    if start:
        gen = pagegenerators.PreloadingGenerator(pagegenerators.AllpagesPageGenerator(start=start,includeredirects=False))
    elif newpages:
        def wrapper_gen():
            for (page, length) in pywikibot.getSite().newpages(500):
                yield page
        gen = wrapper_gen()
    elif longpages:
        def wrapper_gen():
            for (page, length) in pywikibot.getSite().longpages(500):
                yield page
        gen = wrapper_gen()
    elif len(title) != 0:
        title = ' '.join(title)
        gen = [pywikibot.Page(pywikibot.getSite(),title)]
    elif category:
        print "using cat", category
        cat = catlib.Category(pywikibot.getSite(), category)
        gen_ = pagegenerators.CategorizedPageGenerator(cat, recurse=True)
        gen = pagegenerators.PreloadingGenerator(gen_)
    else:
        pywikibot.showHelp()
        show_help()
        return

    if blacklistfile:
        sp.blacklistfile = blacklistfile

    print "Using blacklistfile: %s" % (sp.blacklistfile)
    sp.blackdic = {}
    readBlacklist(sp.blacklistfile, sp.blackdic)
    run_bot(gen, sp, collectFirst)

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()

