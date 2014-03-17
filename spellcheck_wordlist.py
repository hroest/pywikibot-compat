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

import wikipedia as pywikibot
import pagegenerators, catlib

from spellcheck_blacklist import readBlacklist

class BlacklistChecker():

    def __init__(self):
        self.replace = {}
        self.noall = []
        self.rcount = {}
        self.replaceDerivatives = {}

    def searchNreplace(self, wrong, correct):
        """ Uses the Wikipedia search tool to retrieve all pages that contain the
        wrong word and go through them one by one.
        """
        replacedic = self.replaceDerivatives
        s = pagegenerators.SearchPageGenerator(wrong, namespaces='0')
        gen = pagegenerators.PreloadingGenerator(s)
        for page in gen:

            print page
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
                if not replacedic.has_key(wrong): 
                    replacedic[wrong] = correct
                if not self.rcount.has_key(wrong): 
                    self.rcount[wrong] = 0
                self.rcount[wrong] += 1
                page.put_async(newtext, 
                   comment="Tippfehler entfernt: %s -> %s" % (wrong, correct) )


def show_help():
    thishelp = u"""
Arguments for the Review Bot:

-searchWiki:       Use the internal search functionality to find pages for replacement

-blacklist:        Provide a list of wrong words (provide the wrong and the correct word per line separated by ;)

-singleword:       To search and replace a single word use "wrongword;correctword"

    """
    print thishelp

def main():
    ###################################################################
    #                           MAIN                                  #
    ###################################################################
    searchWiki = False
    singleWord = None
    blacklistfile = None

    for arg in pywikibot.handleArgs():
        if arg.startswith("-blacklist:"):
            blacklistfile = arg[11:]
        if arg.startswith("-singleword:"):
            singleWord = arg[12:]
        elif arg.startswith("-searchWiki"):
            searchWiki = True
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
                blacklistChecker.searchNreplace(wrong, correct)

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()

