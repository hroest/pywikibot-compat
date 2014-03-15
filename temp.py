#!/usr/bin/python
# -*- coding: utf-8  -*-

import re
import wikipedia
import range as ranges

import wikipedia as pywikibot
import pagegenerators
class Blacklistchecker():
    def __init__(self):
        pass
    def checkit(self, pages, wrongs, correct, replacedic, noall, replacecount, sp):
        for i,page in enumerate(pages):
            wrong = wrongs[i]
            #wrong = wrong.decode('utf8')
            if wrong in noall: continue
            try:
                text = page.get()
            except pywikibot.NoPage:
                pywikibot.output(u"%s doesn't exist, skip!" % page.title())
                continue
            except pywikibot.IsRedirectPage:
                pywikibot.output(u"%s is a redirect, get target!" % page.title())
                page = page.getRedirectTarget()
                text = page.get()

            myranges = sp.forbiddenRanges(text)
            r = ranges.Ranges()
            r.ranges = myranges
            ext_r = r.get_large_ranges()

            wupper = wrong[0].upper() + wrong[1:]
            wlower = wrong[0].lower() + wrong[1:]
            cupper = correct[0].upper() + correct[1:]
            clower = correct[0].lower() + correct[1:]

            pos = 0
            newtext = text[:]
            while True:
                found = newtext.find( wupper, pos)
                pos += found + 1
                if found in ext_r: continue
                if found == -1: break
                newtext = newtext[:found] + cupper + newtext[found+len(wupper):]
            #newtext = text.replace(wupper, cupper)
            mywrong = wupper
            if newtext == text:
                pos = 0
                newtext = text[:]
                while True:
                    found = newtext.find( wlower, pos)
                    pos += found + 1
                    if found in ext_r: continue
                    if found == -1: break
                    newtext = newtext[:found] + clower + newtext[found+len(wlower):]
                #newtext = text.replace(wlower, clower)
                mywrong = wlower
                if newtext == text: continue

            print page, wrong, correct
            if not replacecount.has_key(mywrong): replacecount[mywrong] = 0
            pywikibot.showDiff(text, newtext)
            self.ask_user_input(page, noall, replacedic, mywrong, correct, replacecount, newtext, text)

    def ask_user_input(self, page, noall, replacedic, wrong, correct, replacecount, newtext, text):
        mynewtext = newtext
        mycomment = "Tippfehler entfernt: %s -> %s" % (wrong, correct)
        correctmark = False
        while True:
            choice = pywikibot.inputChoice('Commit?',
               ['Yes', 'yes', 'No', 'Yes to all', 'No to all',
                'replace with ...', '<--!sic!-->'],
                           ['y', '\\', 'n','a', 'noall', 'r', 's'])
            if choice == 'noall':
                print 'no to all'
                noall.append( wrong )
                return
            elif choice in ('y', '\\'):
                if not replacedic.has_key(wrong) and not correctmark:
                    replacedic[wrong] = correct
                if not correctmark: replacecount[wrong] += 1
                page.put_async(mynewtext, comment=mycomment)
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
            else: return

    def searchNreplace(self, wrong, correct, replacedic):
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

    def searchDerivatives(self, wrongs, corrects, cursor, replaceDerivatives, notlike=''):
        q = """ select * from hroest.countedwords
        where word like '%s'
        and word not like '%s'
        order by occurence DESC; """ % (wrongs+'%', notlike)
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
                if not replaceDerivatives.has_key(wrongs):
                    replaceDerivatives[wrongs] = corrects
