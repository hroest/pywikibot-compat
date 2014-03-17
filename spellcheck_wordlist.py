#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
This bot spellchecks Wikipedia pages using a list of bad words. 
"""

#
# Distributed under the terms of the MIT license.
#

import time
import re
import wikipedia as pywikibot
import pagegenerators, catlib

from spellcheck_blacklist import readBlacklist
from SpellcheckLib import WrongWord
from SpellcheckLib import abstract_Spellchecker
from SpellcheckLib import CallbackObject, Word

from SpellcheckLib import InteractiveWordReplacer
from SpellcheckLib import BlacklistSpellchecker
from SpellcheckLib import collectBlacklistPages

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

def show_help():
    thishelp = u"""
Arguments for the Review Bot:

-searchWiki:       Use the internal search functionality to find pages for replacement. This will perform a simple search and replace (no text parsing)

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
    title = []

    for arg in pywikibot.handleArgs():
        if arg.startswith("-blacklist:"):
            blacklistfile = arg[11:]
        elif arg.startswith("-singleword:"):
            singleWord = arg[12:]
        elif arg.startswith("-searchWiki"):
            searchWiki = True
        elif arg.startswith("-cat:"):
            category = arg[5:]
        elif arg.startswith('-h') or arg.startswith('--help'):
            pywikibot.showHelp()
            show_help()
            return
        else:
            title.append(arg)

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
        # Simple search and replace ...
        for wrong, correct in wordlist.iteritems():
            print "== Replace %s with %s" % (wrong, correct)
            s = pagegenerators.SearchPageGenerator(wrong, namespaces='0')
            gen = pagegenerators.PreloadingGenerator(s)
            blacklistChecker.simpleReplace(gen, wrong, correct)
        return
    elif category:
        print "using cat", category
        cat = catlib.Category(pywikibot.getSite(), category)
        gen_ = pagegenerators.CategorizedPageGenerator(cat, recurse=True)
        gen = pagegenerators.PreloadingGenerator(gen_)
    elif len(title) != 0:
        title = ' '.join(title)
        gen = [pywikibot.Page(pywikibot.getSite(),title)]
    else:
        print "No input articles selected. Abort."
        return

    collectFirst = True
    sp = BlacklistSpellchecker()
    sp.blackdic = wordlist
    collectedPages, nrpages = collectBlacklistPages(-1, gen, sp.blackdic)
    InteractiveWordReplacer().processWrongWordsInteractively(collectedPages)

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()

