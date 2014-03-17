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
from InteractiveWordReplacer import WrongWord

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

def collectBlacklistPages(batchNr, gen, blackdic):
    """ We go through the whole batch and check the content
    at least we have a nice progress bar for the user
    """
    wrongWords = []
    # Start loop
    seenAlready = {}
    for i, page in enumerate(gen):

        try:
            if not page.namespace() == 0: 
                continue
        except TypeError:
            # Its a database object
            if not page.namespace == '0':
                continue

        if page.title() in seenAlready: 
            continue
        seenAlready[ page.title() ] = 0 # add to seen already

        # Get text
        try:
            text = page.get()
        except pywikibot.NoPage:
            pywikibot.output(u"%s doesn't exist, skip!" % page.title())
            continue
        except pywikibot.IsRedirectPage:
            pywikibot.output(u"%s is a redirect, skip!" % page.title())
            continue

        # Process page
        page.words = BlacklistSpellchecker().spellcheck_blacklist(text, blackdic, return_words=True)

        if not len(page.words) == 0: 
            wrongWords.append(page)

        if batchNr > 0 and i > batchNr: 
            break

    return wrongWords, i

class Spellchecker(abstract_Spellchecker):
    """ Blacklist based spellchecker

    This spellchecker reads in a "blacklist" of words that are commonly spelled
    wrong and checks a gien text against this list.
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
    # XML functions
    #
    # Call this function to work on an XML file
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
                res, nrpages = collectBlacklistPages(nrpages, generator, self.blackdic)
            import pickle
            f = open( 'spellcheck_whole.dump', 'w')
            pickle.dump(res, f)
            f.close()
            return

        # TODO load again the dumped result ...
        #f = open( 'spellcheck_whole.dump'); test = pickle.load(f)

        # Loop:
        # - process a batch of pages
        # - work on them interactively
        while True:
            wrongWords, nrpages = collectBlacklistPages(batchNr, generator, self.blackdic)

            print('Found %s wrong words.' % len(wrongWords))
            wr.processWrongWordsInteractively( wrongWords )

            choice = pywikibot.inputChoice('Load next batch?',
                   ['Yes', 'yes', 'No'], ['y', '\\', 'n'])
            if choice == 'n': 
                break

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

    #
    # Database functions
    #

    # Step 1: call this function to store the found words in the database
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
            ww = BlacklistSpellchecker().spellcheck_blacklist( page.text, self.blackdic)
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

    # Step 2: call this function to retrieve the found words from the database
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
            ww = BlacklistSpellchecker().spellcheck_blacklist( page.text, self.blackdic)
            if not len(ww) == 0: wrongWords.append([page, ww])
            if i % 10000 == 0:
                print i
                end = time.time()
                print "%.2f m = %s s" % ( (end- start) /(60.0) ,end- start   )
            i += 1
        return wrongWords, i

def run_bot(allPages, sp):
    start = time.time()
    collectedPages, nrpages = collectBlacklistPages(-1, allPages, sp.blackdic)
    print "==================================="
    print "Processing %s pages took %0.4fs" % (len(collectedPages), time.time() - start)
    InteractiveWordReplacer().processWrongWordsInteractively(collectedPages)

def show_help():
    thishelp = u"""
Arguments for the Review Bot:

-start:            Start spellchecking with this page

-longpages:        Work on pages from Special:Longpages.

-blacklist:        Provide a list of wrong words (provide the wrong and the correct word per line separated by ;)

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
    run_bot(gen, sp)

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()

