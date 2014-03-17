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
import pagegenerators

from spellcheck_hunspell import abstract_Spellchecker
from spellcheck_hunspell import Word
from spellcheck_hunspell import CallbackObject

class WrongWord(Word):

    def __init__(self, wrong_word, location=-1, bigword='', correctword='',
                doReplace=False):
        self.location = location
        self.bigword = bigword
        self.correctword = correctword
        self.doReplace = doReplace

        Word.__init__(self, wrong_word)

class InteractiveWordReplacer(abstract_Spellchecker):
    """ Interactive replace of individual words
    """

    def __init__(self, xmldump=None):
        self.ignorePages = []
        self.ignorePerPages = {}

        self.Callbacks = []

    def processWrongWordsInteractively(self, pages, offline=False):
        """This will process pages with wrong words.

        It expects a list of pages with words attached to it.
        It calls checkSpellingBlack
        It calls doReplacement
        """
        #here we ask the user for input
        self.performReplacementList = []
        self.dontReplace = []
        ask = True
        gen = pagegenerators.PreloadingGenerator(pages)
        for page in gen:
            print('Processing Page = %s'% page.title() )
            thisReplace = []
            try:
                text = page.get()
            except pywikibot.NoPage:
                pywikibot.output(u"%s doesn't exist, skip!" % page.title())
                continue
            except pywikibot.IsRedirectPage:
                pywikibot.output(u"%s is a redirect, get target!" % page.title())
                oldpage = page
                page = page.getRedirectTarget()
                page.words = oldpage.words
                text = page.get()

            text = page.get()
            self.dontReplace = self.checkSpellingBlack(page, self.dontReplace)
            newtext = self.doReplacement(text, page)

            if text == newtext: 
                continue

            pywikibot.showDiff(text, newtext)
            if ask: choice = pywikibot.inputChoice('Commit?',
               ['Yes', 'yes', 'No', 'Yes to all'], ['y', '\\', 'n','a'])
            else: choice = 'y'
            #if choice == 'a': stillAsk=False; choice = 'y'
            if choice in ('y', '\\'):
                callb = CallbackObject()
                self.Callbacks.append(callb)
                page.put_async(newtext, comment=page.typocomment, callback=callb)

    def checkSpellingBlack(self, page, dontReplace):
        """Interactively goes through all wrong words in a page.

        All we do here is save doReplace = True if we want to replace it, while
        doReplace will do the actual replacement.
        Uses self.ignorePerPages and a local dontReplace
        """

        title = page.title()
        text = page.get()
        words = page.words
        for w in words: 
            w.doReplace = False

        # Go through all wrong words in this page
        for w in words:
            smallword = w.word

            # Check if on ignore list
            if self.ignorePerPages.has_key(title) \
               and smallword in self.ignorePerPages[title]: 
                continue

            bigword = Word(w.bigword)
            loc = w.location

            # Try to find replacement site
            w.site = text.find( bigword.word, loc )
            if w.site == -1: 
                w.site = text.find( bigword.word)
            if w.site == -1: 
                pywikibot.output(u"Not found any more in %s: %s" % (
                title, bigword.word))
                continue

            # We now have a potential site for replacement
            sugg = w.correctword
            w.LocAdd = len(bigword)
            if smallword[0].isupper(): 
                sugg = sugg[0].upper() + sugg[1:]
            if smallword == sugg: 
                continue;         #unfortunately this happens
            if smallword in dontReplace:
                continue;  #dont always check the same words

            # Print the two words
            pywikibot.output(u"Replace \03{lightred}\"%s\"" % smallword +
              "\03{default} \nby      \03{lightgreen}\"%s\"\03{default}" % sugg)

            # Print context
            pywikibot.output(u"    %s" % text[max(0,w.site-55):w.site+len(w)+55])
            choice = pywikibot.inputChoice('', ['Yes', 'yes', 'No',
               'No but dont save', 'Replace by something else',
                'Exit and go to next site'], ['y', '\\', 'n', 'b', 'r', 'x'])

            # Evaluate user choice
            if choice == 'b':
                if self.ignorePerPages.has_key( title ):
                    self.ignorePerPages[title].append( smallword)
                else: self.ignorePerPages[ title ] = [ smallword ]
            if choice == 'n': dontReplace.append(w.word); continue
            if choice == 'x': self.ignorePages.append( title ); return dontReplace
            if choice == 'r':
                w.replacement = pywikibot.input(u"What should I replace \"%s\" by?"
                                              % bigword.word)
                w.doReplace = True
            if choice in ( 'y','\\'):
                w.replacement = bigword.replace(sugg)
                w.doReplace = True

        return dontReplace

    def doReplacement(self, text, page, ask = True):
        """This will perform the replacement for one page and return the text.
        """

        page.typocomment  = u"Tippfehler entfernt: "

        #now we have the text, lets replace the word
        for i, word in enumerate(page.words):
            if not word.doReplace: 
                continue

            self.performReplacementList.append(word)

            # Try to find replacement site (text may have changed in the meantime)
            site = text.find( word.bigword, word.site )
            if site == -1:
                site = text.find( word.bigword )
            if site == -1: 
                continue

            # now we have the site (page might be changed in meantime)
            loc = site
            replacement = word.replacement
            LocAdd = word.LocAdd

            # Check for cases where the the wrong word is contained in the
            # replacement but already corrected (this may happen if somebody
            # has replaced the text in the meantime). 
            # We would still find the wrong word but should not replace it!
            replacementHere = text.find( replacement )
            while not replacementHere == site and not replacementHere == -1:
                replacementHere = text.find( replacement , replacementHere+1)

            # exclude cases where replacement is contained in wrong word
            if replacementHere == site and word.bigword.find(replacement) == -1:
                continue

            # Replace the text
            text = text[:loc] + replacement + text[loc+LocAdd:]

            if i > 0: 
                page.typocomment += " , "
            page.typocomment += word.word + " => " + word.replacement

        return text

class BlacklistSpellchecker(abstract_Spellchecker):
    """ Blacklist based spellchecker

    This spellchecker reads in a "blacklist" of words that are commonly spelled
    wrong and checks a gien text against this list.

    Possible usage
    >>> sp = BlacklistSpellchecker()
    >>> result = sp.spellcheck_blacklist(text, {'Deuschland' : 'wrong'})
    """

    def __init__(self):
        pass


    def spellcheck_blacklist(self, text, blackdic, return_for_db=False, return_words=False):
        """ Checks a single text against the words in the blacklist and returns
        a list of wrong words.

        Called by doNextBlackBatch or doNextBlackBatch_db or doBlacklistNoninteractively
        """
        # if correct_html_codes:
        #     text = removeHTML(text)

        loc = 0 # the current location in the text we parse
        old_loc = 0
        curr_r = 0
        ranges = self.forbiddenRanges(text)
        ranges = sorted(ranges)
        wrongWords = []
        prepare = []
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
                if not done and smallword.lower() in blackdic \
                   and not smallword == '' and not smallword.isupper():

                    if not smallword == blackdic[smallword.lower()]:
                        if return_words:
                            wrongWords.append(
                                WrongWord(wrong_word = smallword,
                                          location = loc, 
                                          bigword = bigword.word,
                                          correctword = blackdic[smallword.lower()]
                                ) 
                            )
                        else:
                            wrongWords.append([smallword, bigword, loc, blackdic[smallword.lower()],
                                text[max(0, loc-100):min(loc+100, len(text))] ])

            loc += LocAdd
        return wrongWords

if __name__ == "__main__":
    pass
