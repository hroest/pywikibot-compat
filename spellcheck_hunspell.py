#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
This bot spellchecks Wikipedia pages. It is very simple, only checking
whether a word, stripped to its 'essence' is in the list or not, it does
not do any grammar checking or such. It can be used in four ways:

spellcheck.py Title
    Check a single page; after this the bot will ask whether you want to
    check another page
spellcheck.py -start:Title
    Go through the wiki, starting at title 'Title'.
spellcheck.py -newpages
    Go through the pages on [[Special:Newpages]]
spellcheck.py -longpages
    Go through the pages on [[Special:Longpages]]

For each unknown word, you get a couple of options:
    numbered options: replace by known alternatives
    a: This word is correct; add it to the list of known words
    c: The uncapitalized form of this word is correct; add it
    i: Do not edit this word, but do also not add it to the list
    p: Do not edit this word, and consider it correct for this page only
    r: Replace the word, and add the replacement as a known alternative
    s: Replace the word, but do not add the replacement
    *: Edit the page using the gui
    g: Give a list of 'guessed' words, which are similar to the given one
    x: Ignore this word, and do not check the rest of the page

When the bot is ended, it will save the extensions to its word list;
there is one word list for each language.

The bot does not rely on Latin script, but does rely on Latin punctuation.
It is therefore expected to work on for example Russian and Korean, but not
on for example Japanese.

Command-line options:
-html           change HTML-entities like &uuml; into their respective letters.
               This is done both before and after the normal check.
-knownonly     only check words that have been marked as a mis-spelling in
               the spelling list; words that are not on the list are skipped
-knownplus     finds words in the same way as knownonly, but once a word to
               be changed has been found, also goes through the rest of the
               page.
"""

"""
To install hunspell, you need to install the libhunspell as well as pyhunspell:
sudo apt-get install libhunspell-dev
wget http://pyhunspell.googlecode.com/files/hunspell-0.1.tar.gz
tar xzvf hunspell-0.1.tar.gz; cd hunspell-0.1/
sudo python setup.py install

# then you need to install the dictionaries in your language: 
sudo apt-get install hunspell-de-de-frami 
sudo apt-get install hunspell-de-ch-frami 

"""
#
# (C) Andre Engels, 2005
# (C) Pywikipedia bot team, 2006-2011
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import re, sys
import string, codecs
import hunspell, webbrowser
import xmlreader
import pickle
import wikipedia as pywikibot
import pagegenerators
import time

import pagegenerators, catlib

from spellcheck import SpecialTerm, distance, getalternatives, cap, uncap
from spellcheck import removeHTML, Word, askAlternative
from spellcheck import edit, endpage

from SpellcheckLib import abstract_Spellchecker
from SpellcheckLib import CallbackObject

de_CH_dictionaries = ['/usr/share/hunspell/de_CH.dic', '/usr/share/hunspell/de_CH.aff']
de_DE_dictionaries = ['/usr/share/hunspell/de_DE.dic', '/usr/share/hunspell/de_DE.aff']

correct_html_codes = False
newwords = []
knownonly = False

hunspellEncoding = 'ISO-8859-15'

class Spellchecker(abstract_Spellchecker):

    def __init__(self, hunspell=True, xmldump=None):
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
        self.unknown_words = []
        #
        self.nosugg = []
        self.encounterOften = []
        self.replaceBy = {}
        self.blackdic = {}
        self.Callbacks = []
        self.gen = []
        self.minimal_word_size = 0
        self.nosuggestions = False
        if hunspell: self._init_hunspell()

    def _init_hunspell(self):
        self.filename = 'xml_dumps/dewiki-20090512_Rechtschreibung'
        self.mysite = pywikibot.getSite()
        self.huns_dede = hunspell.HunSpell(de_DE_dictionaries[0], de_DE_dictionaries[1])
        self.huns_dech = hunspell.HunSpell(de_CH_dictionaries[0], de_CH_dictionaries[1])

    # we need to reset the unknown/known number before starting a new cycle!!
    def askUser(self, text, title):
        """Interactive part of the spellcheck() function.
        It uses the unknown words found before to make suggestions:
            - self.unknown_words
            - self.nosugg

        calls askAlternative to figure out what the user wants.
        """
        orig_len = len(text) +1 #plus one because of trailing \np
        for word in self.unknown_words:
            w = word.derive()
            if w in self.nosugg: pywikibot.output(u"\03{lightred}\"%s\"\03{default}" % w +
                u" skipped because no suggestions were found --> it is " +
                    u"assumed to be a name " );
            else:
                bigword = word
                sugg = bigword.suggestions
                loc = bigword.location
                # this should be right here, but we still have to search for it
                # if we changed the text then we need to account for that
                site = text.find( word.word , loc + len(text) - orig_len )

                LocAdd = len(word)
                if site == -1:
                    pywikibot.output(u"\03{lightred}error\03{default}, could" +
                                     "not find \"%s\" anymore" % w)
                    continue
                replacement = askAlternative(bigword,title=title,replaceBy=self.replaceBy,context=text[max(0,site-55):site+len(w)+55])

                if replacement == edit:
                    newtxt = self.saveEditArticle(text, jumpIndex = 0, highlight = w)
                    if newtxt:
                        text = newtxt
                elif replacement == endpage:
                    break
                else:
                    replacement = word.replace(replacement)
                    text = text[:site] + replacement + text[site+LocAdd:]
        return text

    # this tries to edit articles safely
    # some gothic characters cause problems and raise
    # a value error which then causes the whole program to
    # crash -> here we catch those exceptions
    def saveEditArticle(self, text, jumpIndex = 0, highlight = ''):
        import editarticle
        editor = editarticle.TextEditor()
        try:
            newtxt = editor.edit(text, jumpIndex = jumpIndex, highlight = highlight)
        except ValueError:
            #now we try without the last couple of chars
            #this is a hack to find out where to cut since we are
            #probably dealing with IW links
            if not text.find('[[Kategorie:') == -1: cut = text.find('[[Kategorie:')
            elif not text.find('[[en:') == -1: cut = text.find('[[en:') == -1
            else: cut = len(text) -600
            try:
                newtxt = editor.edit(text[:cut], jumpIndex = jumpIndex, highlight = highlight)
                newtxt = newtxt + text[cut:]
            except ValueError:
                pywikibot.output(u"\03{lightred}There are unprintable character" +
                     "in the text, I cannot edit, try something" +
                     "different\03{default}");
                return text
        if newtxt:
            return newtxt
        else:
            return text

    def check_with_hunspell(self, word, useCH):
        return self.huns_dede.spell(word) or \
                (useCH and self.huns_dech.spell(word)) 

    def spellcheck(self, page, checknames = True, knownonly = False):
        """Uses hunspell to replace wrongly written words.
        """
        pageskip = []
        text = page
        if correct_html_codes:
            text = removeHTML(text)
        loc = 0
        old_loc = 0
        schweiz_search = "<!--schweizbezogen-->"
        match = re.search(schweiz_search, text)
        useCH = False
        if match:
            useCH = True
        ranges = self.forbiddenRanges(text)
        ranges = sorted(ranges)
        curr_r = 0
        self.time_suggesting = 0
        self.totalWordsChecked = 0
        self.checkWords = 0
        starttime = time.time()
        while True:

            #added / since in german some words are compositions
            wordsearch = re.compile(r'([\s\=\<\>\_]*)([^\s\=\<\>\_/\-]+)')
            match = wordsearch.search(text,loc)
            LocAdd = 0
            if not match:
                # No more words on this page
                print "=" * 75
                print "Time suggesting %0.4f s" % self.time_suggesting
                print "Total time %0.4f s" % (time.time() - starttime)
                print "----------------------"
                print "Time suggesting of total time %0.4f%% " % (self.time_suggesting *100.0 / (time.time() - starttime) )
                break

            curr_r, loc, in_nontext = self.check_in_ranges(ranges, match.start(), match.end(), curr_r, loc)
            if in_nontext:
                continue

            # Split the words up at special places like &nbsp; or – (these will
            # usually not be found in the dictionary)
            spl = re.split('&nbsp;', match.group(2))
            if len(spl) >1: LocAdd = 5
            elif len(spl) == 1:
                spl = re.split(u'–', spl[0])
            ww = spl[0]
            LocAdd += len(ww)+1
            bigword = Word(ww)
            smallword = bigword.derive()

            loc += len(match.group(1))

            self._spellcheck_word(text, smallword, bigword, ww, loc, LocAdd, useCH)

            # proceed to the next location
            loc += LocAdd

        # We are done with all words
        if correct_html_codes:
            text = removeHTML(text)
        pageskip = []
        return text

    def _spellcheck_word(self, text, smallword, bigword, ww, loc, LocAdd, useCH):

            done = False
            try:
                smallword_encoded = smallword.encode(hunspellEncoding)
            except UnicodeEncodeError: 
                print "encodeerro: ", smallword
                return

            smallword_utf8 = smallword.encode('utf8')
            smallword_utf8_prev = text[loc:loc+1].encode('utf8') + smallword_utf8
            smallword_utf8_next = smallword_utf8 + text[loc+LocAdd-1:loc+LocAdd].encode('utf8')

            if not smallword == '' and not smallword.isupper() and \
               not self.check_with_hunspell(smallword_encoded, useCH) and not self.isNewWord(smallword):

                self.totalWordsChecked += 1

                inWW = ww.find(smallword)
                if not inWW == 0:
                    smallword_utf8_prev = ww[inWW].encode('utf8') + smallword_utf8
                if not inWW+len(smallword) >= len(ww):
                    smallword_utf8_next = smallword_utf8 + ww[inWW+len(smallword)].encode('utf8')

                #  If hunspell doesn't know it, doesn't mean it is not correct
                #  This not only reduces the number of words considered to be
                #  incorrect but also makes it much faster since the feature
                #  hunspell.suggest takes most time (~6x speedup).
                #
                #  (a) - we check a whitelist with names and places
                #      - if we encountered it already we can add this one as done
                #
                if (Word(smallword).isCorrect(checkalternative = knownonly) or
                    smallword in self.unknown or smallword in self.encounterOften or
                    smallword in newwords):
                    done = True
                #
                #  (b.1) - we check whether it is a (german) genitive case and
                #  exist in this form in our whitelist, which is without trailing
                #  "es" or "s"
                #
                elif len(smallword) > 3 and ( (smallword[-2:] == 'es' and
                   Word(smallword[:-2]).isCorrect(checkalternative = knownonly)) or
                   (smallword[-1:] == 's' and
                    Word(smallword[:-1]).isCorrect(checkalternative = knownonly))):
                    done = True
                #
                #  (b.2) - we check whether it is a (german) genitive case and
                #  exist in this form in our whitelist, which is without trailing
                #  "es" or "s"
                #
                elif (len(smallword) > 3 and smallword[-2:] == 'er' and
                      Word(smallword[:-2]).isCorrect(checkalternative = knownonly)):
                    done = True
                #
                #  (c) - we check whether it is at the beginning of a sentence and
                #  thus should be capitalized
                #
                elif loc > 2 and text[loc -2:loc-1] == '.':
                    if self.check_with_hunspell(smallword_utf8[0].lower() + smallword_utf8[1:], useCH):
                        done = True
                #
                #  (d) - we check whether it is correct when the previous character
                #  is taken into account
                #
                elif self.check_with_hunspell(smallword_utf8_prev, useCH):
                        done = True
                #
                #  (e) - we check whether it is correct when the following
                #  character is taken into account
                #
                elif self.check_with_hunspell(smallword_utf8_next, useCH):
                        done = True
                #
                #  (f) - we check whether it is following an internal link like [[th]]is
                #
                elif loc > 2 and text[loc-2:loc] == ']]':
                        done = True

                elif len(smallword) < self.minimal_word_size:
                        done = True
                #
                #  (x) - if we found it more than once, its probably correct
                #
                if smallword in self.unknown and not smallword in self.encounterOften:
                    print "Skip word encountered multiple times:", smallword
                    self.encounterOften.append(smallword)
                    self.unknown.remove(smallword)

                if done:
                    return

                #
                #  (x) - now we need to get the suggestions from hunspell
                #      - this takes nearly all time
                if True:
                    self.checkWords += 1
                    pywikibot.output(u"%s.\03{lightred}\"%s\"\03{default} sugg" % (
                        self.checkWords, smallword));
                    t1 = time.time()
                    if self.nosuggestions: sugg = []
                    elif useCH:
                        sugg = self.huns_dech.suggest(smallword_utf8)
                    else:
                       sugg = self.huns_dede.suggest(smallword_utf8)
                    self.time_suggesting += time.time() -t1

                    if not self.nosuggestions and len(sugg) == 0 and not smallword in self.nosugg:
                        self.nosugg.append(smallword)
                    #
                    #  (x) - now we go through the suggestions and see whether our
                    #  word matches some derivative
                    #
                    for i in range(len(sugg)):
                        try:
                            sugg[i] = unicode(sugg[i], 'utf-8')
                        except UnicodeDecodeError:
                            sugg[i] = unicode(sugg[i], 'iso8859-1')
                        if sugg[i] == smallword:
                            print("whats wrong here? we found %s %s" % (
                                sugg[i], smallword) )
                            done = True
                        # also if just the first character is different and at the
                        # beginning of a sentence
                        """
                        if (sugg[i][0].upper() + sugg[i][1:]) == smallword:
                            #If starting a new sentence, it SHOULD be capitalized!
                            if text[loc -2:loc-1] == '.':
                                print("222 %s" % text[loc-100:loc+100])
                                done = True
                        ###check this
                        ###
                        elif sugg[i] == text[loc-1] + smallword:
                            print("223 %s" % text[loc-100:loc+100])
                            #probably an instance of -xxxxx
                            done = True
                        ##also if the next character should be a point and is
                        elif sugg[i] == smallword + '.':
                            print("224 %s" % text[loc-100:loc+100])
                            done = True
                        ##also if the next character should be a dash and is
                        elif sugg[i] == smallword + '-':
                            print("225 %s" % text[loc-100:loc+100])
                            done = True
                        ##also if the previous character should be a dash and is
                        elif sugg[i] == '-' + smallword:
                            print("226 %s" % text[loc-100:loc+100])
                            done = True
                        """

                #######################################################
                #So now we know whether we have found the word or not #
                #######################################################
                if not done:
                    bigword.suggestions = sugg
                    bigword.location = loc
                    self.unknown.append(smallword);
                    self.unknown_words.append(bigword);
            return 

    def save_wordlist(self, filename):
        if self.rebuild:
            l_list = self.knownwords.keys()
            self.l_list.sort()
            f = codecs.open(filename, 'w', encoding = self.mysite.encoding())
        else:
            l_list = self.newwords
            f = codecs.open(filename, 'a', encoding = self.mysite.encoding())

        if l_list == []: l_list = self.unknown
        for word in l_list:
            if self.Word(word).isCorrect():
                if word != self.uncap(word):
                    if self.Word(self.uncap(word)).isCorrect():
                        # Capitalized form of a word that is in the list uncapitalized
                        continue
                f.write("1 %s\n"%word)
            else:
                f.write("0 %s %s\n"%(word," ".join(self.knownwords[word])))

        f.close()

    def save_one(self, filename, l_list):
        f = codecs.open(filename, 'a', encoding = mysite.encoding())
        for word in l_list:
            f.write("1 %s\n"%word)
        f.close()

    def save_zero(self, filename, dic):
        #first comes the wrong entry, then the correct one
        for wrong,correct in dic.iteritems():
            f.write("0 %s %s\n"% (wrong , correct) )
        f.close()

    def isNewWord(self, word):
        for w in newwords:
            if w == word: return True


def show_help():
    thishelp = u"""
Arguments for the Review Bot:

-start:            Start spellchecking with this page

-longpages:        Work on pages from Special:Longpages.

-nosugg:           No suggestions

    """
    print thishelp


def run_bot(allPages, sp):
    Callbacks = []
    stillSkip  = False;
    firstPage = True
    for page in allPages:
        print(page);

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

        choice = "y"
        if not firstPage:
            choice = pywikibot.inputChoice('Continue now with the spellcheck?', ['Yes', 'Reload Text', 'Next', 'Edit Text'], ['y', 'r', 'n', 'e'])

        firstPage = False
        if choice == 'r':
            text = pywikibot.Page(pywikibot.getSite(), page.title()).get()
        elif choice == 'n':
            continue
        elif choice == 'e':
            text = spellcheck.saveEditArticle(text)

        text = sp.spellcheck(text)
        text = sp.askUser(text, page.title())

        sp.unknown = []
        sp.unknown_words = []

        if text == orig_text:
            continue

        pywikibot.output('\03{lightred}===========\nDifferences to commit:\n\03{default}');
        pywikibot.showDiff(orig_text, text)

        choice = pywikibot.inputChoice('Commit?', ['Yes', 'No'], ['y', 'n'])
        if choice == 'y':
            callb = CallbackObject()
            Callbacks.append(callb)
            page.put_async(text, comment="kleine Verbesserungen, Rechtschreibung", callback=callb)

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

    sp = Spellchecker()
    print "got Spellchecker"

    for arg in pywikibot.handleArgs():
        if arg.startswith("-start:"):
            start = arg[7:]
        elif arg.startswith("-cat:"):
            print "cat!"
            category = arg[5:]
        elif arg.startswith("-newpages"):
            newpages = True
        elif arg.startswith("-longpages"):
            longpages = True
        elif arg.startswith("-nosugg"):
            sp.nosuggestions = True
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
        site = pywikibot.getSite()
        cat = catlib.Category(site, category)
        gen = pagegenerators.CategorizedPageGenerator(cat)
    else:
        ####################################
        #Examples
        site = pywikibot.getSite()
        cat = catlib.Category(site,'Kategorie:Staat in Europa')
        gen = pagegenerators.CategorizedPageGenerator(cat)

    run_bot(gen, sp)

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()

