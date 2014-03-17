#!/usr/bin/python
# -*- coding: utf-8  -*-

import re
import wikipedia
import range as ranges

import wikipedia as pywikibot
import pagegenerators
class Blacklistchecker():

    def __init__(self, load=True):
        self.replace = {}
        self.noall = []
        self.rcount = {}
        self.replaceDerivatives = {}
        if load:
            self.load_wikipedia()


    def checkit(self, pages, wrongs, correct, spellchecker):
        """
        Takes a list of pages and associated wrong words and goes through them
        one by one.
        """
        replacedic = self.replace
        noall = self.noall
        replacecount = self.rcount

        for i,page in enumerate(pages):
            print "Starting work on", page.title()
            wrong = wrongs[i]
            #wrong = wrong.decode('utf8')
            print wrong, "in self.noall ", wrong in self.noall
            if wrong in self.noall: continue
            try:
                text = page.get()
            except pywikibot.NoPage:
                pywikibot.output(u"%s doesn't exist, skip!" % page.title())
                continue
            except pywikibot.IsRedirectPage:
                pywikibot.output(u"%s is a redirect, get target!" % page.title())
                page = page.getRedirectTarget()
                text = page.get()

            print "got text.."
            myranges = spellchecker.forbiddenRanges(text)
            r = ranges.Ranges()
            r.ranges = myranges
            ext_r = r.get_large_ranges()

            wupper = wrong[0].upper() + wrong[1:]
            wlower = wrong[0].lower() + wrong[1:]
            cupper = correct[0].upper() + correct[1:]
            clower = correct[0].lower() + correct[1:]

            pos = 0 
            newtext = text[:]
            print "start finding position...", page.title(), wupper
            while True: 
                found = newtext.find( wupper, pos)
                pos += found + 1
                print pos, len(ext_r)
                if found in ext_r and found != -1: continue
                if found == -1: break
                newtext = newtext[:found] + cupper + newtext[found+len(wupper):]
            #newtext = text.replace(wupper, cupper)
            mywrong = wupper
            if newtext == text: 
                pos = 0 
                newtext = text[:]
                print "start finding position...", page.title(), wlower
                while True: 
                    found = newtext.find( wlower, pos)
                    pos += found + 1
                    print pos, len(ext_r)
                    if found in ext_r and found != -1: continue
                    if found == -1: break
                    newtext = newtext[:found] + clower + newtext[found+len(wlower):]
                #newtext = text.replace(wlower, clower)
                mywrong = wlower
                if newtext == text: continue

            print page, wrong, correct
            if not replacecount.has_key(mywrong): replacecount[mywrong] = 0
            pywikibot.showDiff(text, newtext)
            self.ask_user_input(page, mywrong, correct, newtext, text)

    def ask_user_input(self, page, wrong, correct, newtext, text):
        """
        Takes a page and a list of words to replace and asks the user for each one
        """
        replacedic = self.replace
        noall = self.noall
        replacecount = self.rcount
        mynewtext = newtext
        mycomment = "Tippfehler entfernt: %s -> %s" % (wrong, correct) 
        correctmark = False
        while True:
            choice = pywikibot.inputChoice('Commit?', 
               ['Yes', 'yes', 'No', 'Yes to all', 'No to all', 
                'replace with ...', 'replace always with ...', '<--!sic!-->'], 
                           ['y', '\\', 'n','a', 'noall', 'r', 'ra', 's'])
            if choice == 'noall':
                print 'no to all'
                self.noall.append( wrong )
                return
            elif choice in ('y', '\\'):
                if not replacedic.has_key(wrong) and not correctmark:
                    replacedic[wrong] = correct
                if not correctmark: replacecount[wrong] += 1
                print "putting page"
                page.put_async(mynewtext, comment=mycomment)
                #page.put(mynewtext, comment=mycomment)
                print "put page"
                return
            elif choice == 's':
                mynewtext = text.replace(wrong, wrong + '<!--sic!-->')
                pywikibot.showDiff(text, mynewtext)
                mycomment = "Korrektschreibweise eines oft falsch geschriebenen Wortes (%s) markiert." % (wrong) 
                correctmark = True
            elif choice == 'r':
                replacement = pywikibot.input('Replace "%s" with?' % wrong)
                mynewtext = text.replace(wrong, replacement)
                if mynewtext == text: return
                pywikibot.showDiff(text, mynewtext)
                mycomment = "Tippfehler entfernt: %s -> %s" % (wrong, replacement) 
            elif choice == 'ra': pass #TODO
            else: return

    def searchNreplace(self, wrong, correct):
        replacedic = self.replaceDerivatives
        s = pagegenerators.SearchPageGenerator(wrong, namespaces='0')
        gen = pagegenerators.PreloadingGenerator(s)
        for page in gen:
            text = page.get()
            newtext = text.replace(wrong, correct)
            if newtext == text: continue
            print page
            pywikibot.showDiff(text, newtext)
            choice = pywikibot.inputChoice('Commit?', 
               ['Yes', 'yes', 'No', 'Yes to all'], ['y', '\\', 'n','a'])    
            if choice in ('y', '\\'):
                if not replacedic.has_key(wrong): replacedic[wrong] = correct
                page.put_async(newtext, 
                   comment="Tippfehler entfernt: %s -> %s" % (wrong, correct) )

    def searchDerivatives(self, wrongs, corrects, cursor, notlike='', db='hroest.countedwords'):
        q = """ select * from %s
        where word like '%s' 
        and word not like '%s'
        order by occurence DESC; """ % (db, wrongs+'%', notlike) 
        cursor.execute( q )
        allwrong = cursor.fetchall()
        for wrong in allwrong:
            wrong = wrong[1]
            wrong = wrong.decode('utf8')
            correct = wrong.replace( wrongs, corrects)
            correct = correct.decode('utf8')
            if correct == wrong: 
                correct = wrong.replace( wrongs[1:], corrects[1:])
            print wrong, correct
            testdic = {}
            self.searchNreplace(wrong, correct, testdic)
            if len(testdic) > 0:
                if not self.replaceDerivatives.has_key(wrongs): 
                    self.replaceDerivatives[wrongs] = corrects


    def find_candidates(self, myw, cursor, 
                        occurence_cutoff = 20, lcutoff = 0.8,
                        db='hroest.countedwords'):
        import Levenshtein
        # \xc2\xad is a soft hyphen that is sometimes used instaed of a space
        # 
        # Search for all words that start with the same 3 chars
        # then 
        sterm = myw[:3]
        l = len(myw)
        cursor.execute(
        """
        select * from %s where word like '%s' 
        #and length(word) between %s and %s
        and word not like '%s'
        order by word 
        """ % (db, sterm.encode('utf8')+'%', l-2, l+2, myw.encode('utf8')+'%') )
        similar = cursor.fetchall()
        #original = [s for s in similar if s[1] == myw][0]
        #original_count = original[0]
        candidates = [s[1] for s in similar if 
                      Levenshtein.ratio(myw,s[1].decode('utf8')) > lcutoff and
                      s[1] != myw #and s[0] *1.0 / original_count < 1e-3]
                      and s[0] < occurence_cutoff and not '\xc2\xad' in s[1]] 
        # Search for all words that start with the same char and end with the same 3 chars
        sterm = myw[0] + '%' + myw[-3:]
        cursor.execute(
        """
        select * from %s where word like '%s' 
        #and length(word) between %s and %s
        and word not like '%s'
        order by word 
        """ % (db, sterm.encode('utf8')+'%', l-2, l+2, myw.encode('utf8')+'%') )
        similar = cursor.fetchall()
        #original = [s for s in similar if s[1] == myw][0]
        #original_count = original[0]
        candidates.extend(  [s[1] for s in similar if 
                      Levenshtein.ratio(myw,s[1].decode('utf8')) > lcutoff and
                      s[1] != myw #and s[0] *1.0 / original_count < 1e-3]
                      and s[0] < occurence_cutoff and not '\xc2\xad' in s[1]] )
        #get unique ones
        return list(set( candidates ) )

    def load_candidates(self, correct, candidates):
        import spellcheck
        pages = []
        print "Enter numbers separated with a space" 
        for i, wrong in enumerate(candidates): 
            wrong = wrong.decode('utf8')
            if wrong in self.noall: continue
            if correct.find(wrong) != -1: continue
            print i, wrong
        #
        toignore = pywikibot.input('Ignore?')
        toignore = [candidates[int(t)].decode('utf8') for t in toignore.split(' ') if t != '']
        self.noall.extend(toignore)

        for i, wrong in enumerate(candidates):
            wrong = wrong.decode('utf8')
            if correct.find(wrong) != -1: continue
            if wrong in self.noall: continue
            s = list(pagegenerators.SearchPageGenerator(wrong, namespaces='0'))
            print wrong, len(list(s))
            if len(list(s)) > 90:
                s = list(pagegenerators.SearchPageGenerator("%s" % wrong, namespaces='0'))
                print "now we have ", len(s), " found"
                if len(list(s)) > 90: s = s[:5]
            for p in s: 
                p.wrong = wrong;
                p.words = [ spellcheck.WrongWord(wrong, bigword=wrong, correctword=correct) ]
                print "append page", p
                pages.append(p)
        return pages

    def load_wikipedia(self):
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
            spl =  l.split(':')
            mycount[spl[0].strip()] = int(spl[1].strip() )
        mypage = pywikibot.Page(pywikibot.getSite(), 'User:HRoestTypo/replacedDerivatives')
        text = mypage.get()
        lines = text.split('* ')[1:]
        myreplacedd = {}
        for l in lines:
            spl =  l.split(' : ')
            myreplacedd[spl[0]] = spl[1].strip()

        self.replace = myreplace
        self.noall = mycorrect
        self.rcount = mycount
        self.replaceDerivatives = myreplacedd

    def store_wikipedia(self):
        replace = self.replace
        noall = self.noall
        rcount = self.rcount
        replaceDerivatives = self.replaceDerivatives

        s = ''
        for k in sorted(replace.keys()):
            s += '* %s : %s\n' % (k, replace[k])
        mypage = pywikibot.Page(pywikibot.getSite(), 'User:HRoestTypo/replaced')
        mypage.put_async( s )
        s = ''
        for k in sorted(noall):
            s += '* %s \n' % (k)
        mypage = pywikibot.Page(pywikibot.getSite(), 'User:HRoestTypo/correct')
        mypage.put_async( s )
        s = ''
        for k in sorted(rcount.keys()):
            if rcount[k] > 0: s += '* %s : %s\n' % (k, rcount[k])
        mypage = pywikibot.Page(pywikibot.getSite(), 'User:HRoestTypo/replacCount')
        mypage.put_async( s )
        s = ''
        for k in sorted(replaceDerivatives.keys()):
            s += '* %s : %s\n' % (k, replaceDerivatives[k])
        mypage = pywikibot.Page(pywikibot.getSite(), 'User:HRoestTypo/replacedDerivatives')
        mypage.put_async( s )

    
