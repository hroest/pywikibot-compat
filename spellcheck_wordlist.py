#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
This bot spellchecks Wikipedia pages using a list of known "bad" words. 
It can be used in the following ways:

spellcheck_wordlist.py Title
    Check a single page
spellcheck_wordlist.py -cat:Category
    Check all pages in the given category (recursively)
python spellcheck_wordlist.py -xmlfile:/path/to/wiki-latest-pages-articles.xml
    Check all pages in the given XML file
python spellcheck_wordlist.py -searchWiki
    Checks all pages containing the wrong word (using the websearch functionality) 

Wordlists can be provided in one of two formats (note: all words need to be in lowercase):
-blacklist:        Provide a file that contains a list of wrong words (provide the wrong and the correct word per line separated by semicolon ";")
-singleword:       To search and replace a single word use "wrongword;correctword"

Command-line options:
-batchNr:          Size of batches for the XML file processing

Example usage:

    spellcheck_wordlist.py -searchWiki -singleword:"Dölli;test"
    spellcheck_wordlist.py Uttwil -singleword:"goldschmied;test"
    spellcheck_wordlist.py -xmlfile:/media/data/tmp/wiki/dewiki-latest-pages-articles.xml.bz2 -singleword:"und;test" -batchNr:10
"""

#
# Distributed under the terms of the MIT license.
#

import wikipedia as pywikibot
import pagegenerators, catlib
import re, string, sys

from SpellcheckLib import Word, WrongWord
from SpellcheckLib import readBlacklist
from SpellcheckLib import InteractiveWordReplacer
from SpellcheckLib import abstract_Spellchecker

NUMBER_PAGES = 500

class BlacklistSpellchecker(abstract_Spellchecker):
    """ Blacklist based spellchecker

    This spellchecker reads in a "blacklist" of words that are commonly spelled
    wrong and checks a gien text against this list.

    Possible usage
    >>> sp = BlacklistSpellchecker()
    >>> result = sp.spellcheck_blacklist(text, {'Deuschland' : 'wrong'})
    """

    def __init__(self):
        self.rcount = {}

    def spellcheck_blacklist(self, text, badDict, return_for_db=False, return_words=False):
        """ Checks a single text against the words in the blacklist and returns
        a list of wrong words.
        """

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

            loc_start = loc + len(match.group(1)) # start of the word
            ww = spl[0]
            LocAdd += len(ww) + 1
            bigword = Word(ww)
            smallword = bigword.derive()


            verb = False
            if smallword == "olg" : 
                verb = True
                print "aa"
                print loc
                print ranges
                print curr_r
                print ranges[curr_r]

            done = False
            for r in ranges:
                # If the end of the range coincides with the start of the word
                # we might not have a full word -> rather discard it.
                if r[1] == loc_start:
                    loc += LocAdd
                    done = True

            if done:
                continue

            # We advance the location by the characters skipped
            loc += len(match.group(1))
            done = self._text_skip(text, loc, smallword)

            ###################################
            #use this code to insert into the database
            if return_for_db:
                if not done:
                    wrongWords.append(smallword)

            else:
                ###################################
                #here we check whether it is wrong
                if not done and smallword.lower() in badDict \
                   and not smallword == '' and not smallword.isupper():

                    if not smallword == badDict[smallword.lower()]:
                        if return_words:
                            wrongWords.append(
                                WrongWord(wrong_word = smallword,
                                          location = loc, 
                                          bigword = bigword.word,
                                          correctword = badDict[smallword.lower()]
                                ) 
                            )
                        else:
                            wrongWords.append([smallword, bigword, loc, badDict[smallword.lower()],
                                text[max(0, loc-100):min(loc+100, len(text))] ])

            loc += LocAdd
        return wrongWords

    def _text_skip(self, text, loc, word):

        done = False

        # if we have ''' before, we dont want to interpret
        if loc > 3 and text[loc-3:loc] == "'''" or \
            text[loc:loc+3] == "'''" :
            done = True

        # if we have a <nowiki></nowiki> break before, we dont want to interpret
        if loc > 17 and text[loc-17:loc] == '<nowiki></nowiki>':
            done = True

        # if we have a closing wikilink "]]" before, we dont want to interpret
        if loc > 2 and text[loc-2:loc] == ']]':
            done = True

        # try to find out whether its an abbreviation and has a '.' without capitalization
        if loc+len(word)+5 < len(text) and \
           text[loc+len(word)] == '.' and \
           text[loc+len(word)+2].islower() and \
           not text[loc+len(word):loc+len(word)+5] == '<ref>':
            done = True

        # words that end with ' or -
        if loc+len(word) < len(text) and text[loc+len(word)] == '-':
            done = True

        #exclude words that have uppercase letters in the middle
        for l in word[1:]:
            if l.isupper(): 
                done=True;

        #exclude words that are smaller than 3 letters
        if len( word.lower() ) < 3: 
            done = True

        return done

    def spellcheck_blacklist_regex(self, text, badDict, return_for_db=False, return_words=False):

        ranges = self.forbiddenRanges(text)
        ranges = sorted(ranges)
        wrongWords = []
        for word, replacement in badDict.iteritems():
            word_re = re.compile(word, re.IGNORECASE)
            allOccurences = [m.start() for m in re.finditer(word_re, text)]
            wordDiff = len(word) - len(replacement)
            currDiff = 0
            for loc in allOccurences:

                # Words that are parts of other words should be ignored
                if not text[loc-1] in string.whitespace:
                    continue

                if self._text_skip(text, loc, text[loc:loc+len(word)]):
                    continue

                done = False
                for r in ranges:
                    if loc > r[0] and loc < r[1]:
                        done = True
                        break

                if not done:
                    wrongWords.append([word, Word(word), loc, badDict[word.lower()],
                      text[max(0, loc-100):min(loc+100, len(text))] ])

        return wrongWords

    def simpleReplace(self, gen, wrong, correct, verbose=True):
        """ Replaces the word by a simple string operation
        wrong word and go through them one by one.
        """

        # Ensure that empty words do not trigger an exception
        if len(wrong) == 0 or len(correct) == 0: 
            return

        for page in gen:

            try:
                text = page.get()
            except pywikibot.NoPage:
                pywikibot.output(u"%s doesn't exist, skip!" % page.title())
                continue
            except pywikibot.IsRedirectPage:
                pywikibot.output(u"%s is a redirect, skip!" % page.title())
                continue

            # First, check whether word is present (allows early exit)
            wrongwords = self.spellcheck_blacklist(text, {wrong : correct}, return_words=True)
            if len(wrongwords) == 0: 
                continue

            InteractiveWordReplacer().processWrongWordsInteractively( [page] )

def collectBlacklistPages(batchNr, gen, badDict):
    """Collect all wrong words in the provided page generator.
    """

    wrongWords = []
    seenAlready = {}

    for i, page in enumerate(gen):

        if not page.namespace() == 0: 
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
        page.words = BlacklistSpellchecker().spellcheck_blacklist(text, badDict, return_words=True)

        if not len(page.words) == 0: 
            wrongWords.append(page)

        if batchNr > 0 and i > batchNr: 
            break

    return wrongWords, i

def processXMLWordlist(xmlfile, badDict, batchNr = 3000, breakUntil = '',
                   doNoninteractive=False):
    from SpellcheckLib import InteractiveWordReplacer
    import xmlreader

    wr = InteractiveWordReplacer()
    generator = xmlreader.XmlDump(xmlfile).parse()

    def collectBlacklistPagesXML(batchNr, gen, badDict):
        """Collect all wrong words in the provided page generator.
        """
        from SpellcheckLib import BlacklistSpellchecker
        wrongWords = []
        seenAlready = {}
        i = 0
        for page in gen:
            if not page.ns == '0':
                continue
            # Process page
            page.words = BlacklistSpellchecker().spellcheck_blacklist(page.text, badDict, return_words=True)
            if not len(page.words) == 0: 
                wrongWords.append(page)
            if batchNr > 0 and i > batchNr: 
                break
            i += 1
        return wrongWords, i

    # Fast-forward until a certain page
    i = 0
    currentpage = None
    if not breakUntil == '':
        for page in generator:
            currentpage = page
            if page.title == breakUntil: 
                break
            i += 1
            if i % 100 == 0:
                sys.stdout.flush()
                sys.stdout.write("\rSearched pages: %s" % i)

    print("\nStarting to work on batches")

    if doNoninteractive:
        nrpages = 10000
        # process all of them, loop until there are no more pages
        while nrpages == 10000:
            res, nrpages = collectBlacklistPagesXML(nrpages, generator, badDict)
        import pickle
        f = open( 'spellcheck_whole.dump', 'w')
        pickle.dump(res, f)
        f.close()
        return

    # Loop:
    # - process a batch of pages
    # - work on them interactively
    while True:
        wrongWords, nrpages = collectBlacklistPagesXML(batchNr, generator, badDict)

        print('Found %s wrong words.' % len(wrongWords))
        res = []
        for p in wrongWords:
            r = pywikibot.Page(pywikibot.getSite(),p.title)
            r.words = p.words
            res.append(r)

        wr.processWrongWordsInteractively( res )

        choice = pywikibot.inputChoice('Load next batch?',
               ['Yes', 'yes', 'No'], ['y', '\\', 'n'])
        if choice == 'n': 
            break

    errors = False
    doneSaving = True
    for call in wr.Callbacks:
        try:
            if not call.error is None:
                print('could not save page %s because\n:%s' % (call.page,
                       call.error)); errors = True
        except AttributeError:
            print('not done yet with saving')
            doneSaving = False

    if not errors and doneSaving:
        print('saved all pages')

def main():
    ###################################################################
    #                           MAIN                                  #
    ###################################################################
    searchWiki = False
    singleWord = None
    blacklistfile = None
    blacklistpage = None
    category = None
    xmlfile = None
    title = []
    batchNr = 1000

    for arg in pywikibot.handleArgs():
        if arg.startswith("-blacklist:"):
            blacklistfile = arg[11:]
            print "blacklist here", blacklistfile 
        elif arg.startswith("-blacklistpage:"):
            blacklistpage = arg[15:]
        elif arg.startswith("-singleword:"):
            singleWord = arg[12:]
        elif arg.startswith("-searchWiki"):
            searchWiki = True
        elif arg.startswith("-xmlfile:"):
            xmlfile = arg[9:]
        elif arg.startswith("-batchNr:"):
            batchNr = int(arg[9:])
        elif arg.startswith("-cat:"):
            category = arg[5:]
        elif arg.startswith('-h') or arg.startswith('--help'):
            pywikibot.showHelp()
            return
        else:
            title.append(arg)

    # This is a purely interactive bot, we therefore do not want to put-throttle
    pywikibot.put_throttle.setDelay(1)

    # Load wordlist
    #  -> this is non-exclusive, e.g. combinations of lists are possible ... 
    wordlist = {}

    if singleWord:
        spl = singleWord.split(";")
        wordlist = dict([  [spl[0].strip(), spl[1].strip()]  ])

    if blacklistfile:
        readBlacklist(blacklistfile, wordlist)

    if blacklistpage:
        mypage = pywikibot.Page(pywikibot.getSite(), blacklistpage)
        text = mypage.get()
        lines = text.split('* ')[1:]
        for l in lines:
            spl =  l.split(' : ')
            wordlist[spl[0].lower()] = spl[1].strip().lower()

    print "Loaded wordlist of size", len(wordlist)

    # Initiate checker
    blacklistChecker = BlacklistSpellchecker()

    if searchWiki:
        # Simple search and replace ...
        for wrong, correct in wordlist.iteritems():
            print "== Replace %s with %s" % (wrong, correct)
            s = pagegenerators.SearchPageGenerator(wrong, namespaces='0')
            gen = pagegenerators.PreloadingGenerator(s, pageNumber=NUMBER_PAGES)
            blacklistChecker.simpleReplace(gen, wrong, correct)
        return
    elif xmlfile:
        if len(title) != 0:
            title = ' '.join(title)
        else:
            title = ""

        processXMLWordlist(xmlfile, wordlist, breakUntil = title, batchNr=batchNr)
    elif category:
        print "using cat", category
        cat = catlib.Category(pywikibot.getSite(), category)
        gen_ = pagegenerators.CategorizedPageGenerator(cat, recurse=True)
        gen = pagegenerators.PreloadingGenerator(gen_, pageNumber=NUMBER_PAGES)
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

