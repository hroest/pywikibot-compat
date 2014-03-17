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

import time
import re
import wikipedia as pywikibot
import pagegenerators, catlib

from spellcheck_blacklist import readBlacklist
from spellcheck_blacklist import WrongWord
from spellcheck_hunspell import abstract_Spellchecker
from spellcheck_hunspell import CallbackObject, Word

from InteractiveWordReplacer import InteractiveWordReplacer
from InteractiveWordReplacer import BlacklistSpellchecker

class BlacklistChecker():

    def __init__(self):
        self.replace = {}
        self.noall = []
        self.rcount = {}
        self.replaceDerivatives = {}

    def simpleReplace(self, gen, wrong, correct, verbose=True):
        """ Replaces the word by a simple string operation
        wrong word and go through them one by one.
        """
        for page in gen:

            try:
                text = page.get()
            except pywikibot.NoPage:
                pywikibot.output(u"%s doesn't exist, skip!" % page.title())
                continue
            except pywikibot.IsRedirectPage:
                pywikibot.output(u"%s is a redirect, skip!" % page.title())
                continue

            # Perform replacement (globally)
            newtext = text
            newtext = newtext.replace(wrong[0].lower() + wrong[1:], correct[0].lower() + correct[1:])
            newtext = newtext.replace(wrong[0].upper() + wrong[1:], correct[0].upper() + correct[1:])

            if newtext == text: 
                continue

            pywikibot.showDiff(text, newtext)
            choice = pywikibot.inputChoice('Commit?', 
               ['Yes', 'yes', 'No', 'No to all'], ['y', '\\', 'n', 'x'])    
            if choice in ('x'):
                return
            if choice in ('y', '\\'):
                if not self.replaceDerivatives.has_key(wrong): 
                    self.replaceDerivatives[wrong] = correct
                if not self.rcount.has_key(wrong): 
                    self.rcount[wrong] = 0
                self.rcount[wrong] += 1
                page.put_async(newtext, 
                   comment="Tippfehler entfernt: %s -> %s" % (wrong, correct) )

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

        wrong_words = sp.spellcheck_blacklist(text, sp.blackdic, return_words = True)
        page.words = wrong_words

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

-searchWiki:       Use the internal search functionality to find pages for replacement

-blacklist:        Provide a list of wrong words (provide the wrong and the correct word per line separated by ;)

-singleword:       To search and replace a single word use "wrongword;correctword"

-cat:              Recursively only work on pages of this category

    """
    print thishelp

def main():
    ###################################################################
    #                           MAIN                                  #
    ###################################################################
    searchWiki = False
    singleWord = None
    blacklistfile = None
    category = None

    for arg in pywikibot.handleArgs():
        if arg.startswith("-blacklist:"):
            blacklistfile = arg[11:]
        if arg.startswith("-singleword:"):
            singleWord = arg[12:]
        elif arg.startswith("-searchWiki"):
            searchWiki = True
        elif arg.startswith("-cat:"):
            category = arg[5:]
        elif arg.startswith('-h') or arg.startswith('--help'):
            pywikibot.showHelp()
            show_help()
            return

    # This is a purely interactive bot, we therefore do not want to put-throttle
    pywikibot.put_throttle.setDelay(1)

    # Load wordlist
    wordlist = {}
    if blacklistfile:
        readBlacklist(blacklistfile, wordlist)
    elif singleWord:
        spl = singleWord.split(";")
        wordlist = dict([  [spl[0].strip(), spl[1].strip()]  ])

    # Initiate checker
    blacklistChecker = BlacklistChecker()

    if searchWiki:
        for wrong, correct in wordlist.iteritems():
            print "== Replace %s with %s" % (wrong, correct)
            s = pagegenerators.SearchPageGenerator(wrong, namespaces='0')
            gen = pagegenerators.PreloadingGenerator(s)
            blacklistChecker.simpleReplace(gen, wrong, correct)
    elif category:
        print "using cat", category
        cat = catlib.Category(pywikibot.getSite(), category)
        gen_ = pagegenerators.CategorizedPageGenerator(cat, recurse=True)
        gen = pagegenerators.PreloadingGenerator(gen_)
        # blacklistChecker.simpleReplace(gen, wrong, correct)

        collectFirst = True
        sp = BlacklistSpellchecker()
        sp.blackdic = wordlist
        run_bot(gen, sp, collectFirst)
    else:
        print "No input articles selected. Abort."

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()

