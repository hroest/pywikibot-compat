#!/usr/bin/python
# -*- coding: utf-8  -*-

"""Unit test for blacklist spellchecker
"""

import wikipedia as pywikibot
import spellcheck_blacklist as spellcheck
import textrange_parser 

import unittest
#from nose.tools import nottest

def getTestCasePhotovolataik():
    """ This test checks that image names are not spellchecked...

    mypage = pywikibot.Page(pywikibot.getSite(), 'Photovoltaik')
    text = mypage.getOldVersion(80189062)
    """

    return u"""
        Nicht zu verwechseln ist „Grid Parity“ jedoch mit einer ...

        == Integration in das Stromnetz ==

        <gallery widths="300" heights="200" perrow="5" caption="Anzahl der PV-Anlagen nach BNetzA">
         Datei:Histogramm_der_PV-Anlagen_Deuschland_Jan2009-Mai2010.jpg‎|Anzahl der installierten Photovoltaikanlagen nach Leistung
        </gallery>

        Die Erzeugung von Solarstrom ist statistisch sehr gut vorhersagbar ([[Log-Normalverteilung]] der Häufigkeitsdichte der  ...
        """

def getTestCasePietismus():
    """ This test checks that poems / quotes are not spellchecked...

    mypage = pywikibot.Page(pywikibot.getSite(), 'Pietismus')
    text = mypage.getOldVersion(79906986)
    """

    return u"""
        Als positive Selbstbezeichnung hat erstmals der pietistische Leipziger Poesie-Professor [[Joachim Feller]] (1638–1691) das Wort „Pietist“ verwendet, ....
        <poem>
        ''Es ist ietzt Stadt-bekannt der Nahm der Pietisten;
        Was ist ein Pietist? Der Gottes Wort studirt/
        Und nach demselben auch ein heilges Leben führt.''
        </poem>
        Im Oktober 1689 folgte Fellers Bekenntnis in dem Sonett auf den verstorbenen Leipziger Kaufmann Joachim Göring (1625–1689): 
        <poem>
        """

def getTestCaseDogville():
    """ This test checks that specifically wrongly spelled names are not corrected

    mypage = pywikibot.Page(pywikibot.getSite(), 'Dogville')
    text = mypage.getOldVersion(79145353)
    """

    return u"""
        * [[Philip Baker Hall]]: Tom Edison Sr.
        * [[Chloë Sevigny]]: Liz Henson
        * [[John Hurt]] als Erzähler (in der Originalfassung) 
        * [[Siobhan Fallon]]: Martha
        }}
        '''Dogville''' ist ein Film von [[Lars von Trier]] ([[Filmjahr 2003|2003]]), produziert im schwedischen [[Trollhättan]]. Das [[Filmdrama]] ist der erste Teil von Von Triers ''USA-Trilogie'', die mit ''[[Manderlay]]'' (2005) fortgesetzt wurde und mit dem im Jahr 2009 geplanten Film ''Wasington''<!-- heisst wirklich so, ohne "h" --> abgeschlossen werden sollte.

        == Handlung ==
        Dogville ist ein abgelegenes Dorf in den Rocky Mountains, während der Zeit der Depression. Ein Einwohner ist der Hobbyschriftsteller Tom Edison. Er will am kommenden Tag vor den Einwohnern einen Vortrag zur Stärkung der Moral halten. Ihm fehlt noch die passende Illustration seiner These, dass die Menschen Probleme im Umgang mit Geschenken hätten. Da taucht eine junge Frau im Dorf auf. Es ist Grace, die von Gangstern verfolgt wird. Tom versteckt sie vor den Gangstern. 
        """

def getTestCaseKarel1():
    """ This test checks that specifically wrongly spelled names are not corrected

    mypage = pywikibot.Page(pywikibot.getSite(), 'Karel De Schrijver')
    text = mypage.getOldVersion(55865499)
    """

    return u"""
        * 1964 ''Kleine Vlaamse Suite''
        *# Heroisch Visioen<!--sic!-->
        *# Rustige Zomeravond
        """

def getTestCaseKarel2():
    """ This test checks that specifically wrongly spelled names are not corrected

    mypage = pywikibot.Page(pywikibot.getSite(), 'Karel De Schrijver')
    text = mypage.getOldVersion(55865499)
    """

    return u"""
        * 1964 ''Kleine Vlaamse Suite''
        *# Heroisch Visioen
        *# Rustige Zomeravond
        """

def getTestCaseKarel3():
    """ This test checks that specifically wrongly spelled names are not corrected

    mypage = pywikibot.Page(pywikibot.getSite(), 'Karel De Schrijver')
    text = mypage.getOldVersion(55865499)
    """

    return u"""
        * 1964 ''Kleine Vlaamse Suite''
        *# Heroisch Visioen<!-- sic! -->
        *# Rustige Zomeravond
        """

# ##########################################################################
# Start of Test
class SpellcheckBlacklistTestCase(unittest.TestCase):

    def setUp(self):
        self.sp = spellcheck.Spellchecker()

    def test_check_in_ranges(self):
        ranges = [[16, 40], [18, 131], [68, 81], [180, 200]]

        curr_r = 0
        loc = 0
        # Match between 0 and 5
        curr_r, loc, in_nontext = self.sp.check_in_ranges(ranges, 0, 5, curr_r, loc)
        assert curr_r == 0
        assert loc == 0
        assert not in_nontext

        # Match between 16 and 17
        curr_r, loc, in_nontext = self.sp.check_in_ranges(ranges, 16, 17, curr_r, loc)
        assert curr_r == 3
        assert loc == 131
        assert in_nontext

        # Match between 140 and 150
        curr_r, loc, in_nontext = self.sp.check_in_ranges(ranges, 140, 150, curr_r, loc)
        assert curr_r == 3
        assert loc == 131
        assert not in_nontext

        # Match between 180 and 190
        curr_r, loc, in_nontext = self.sp.check_in_ranges(ranges, 180, 190, curr_r, loc)
        assert curr_r == 4
        assert loc == 200
        assert in_nontext

    def test_forbiddenRanges(self):
        text = "{{test template }} TEXT {{test2 template}} MORE TEXT"
        res = self.sp.forbiddenRanges(text)
        assert len(res) == 2
        assert res[0] == [0,18]
        assert res[1] == [24,42]
        assert text[18:24] + text[42:] == " TEXT  MORE TEXT"

        # Nested
        text = "{{test template }} TEXT {{test2 template param1 = {{template 3 param_internal = some }} | param2 = other }} MORE TEXT"
        res = self.sp.forbiddenRanges(text)
        assert len(res) == 3
        assert res[0] == [0,18]
        assert res[1] == [50,87]
        assert res[2] == [24,107]
        assert text[18:24] + text[107:] == " TEXT  MORE TEXT"

        # Nested
        text = "{{test template }} TEXT {{test2 param1 = [[test|test2]] }} MORE TEXT \"some quoted\" TEXT <!-- some comment --> FINAL"
        res = self.sp.forbiddenRanges(text)
        assert len(res) == 5
        assert res == [[0, 18], [24, 58], [41, 55], [69, 82], [88, 109]]

    def test_spellcheck_blacklist_1(self):

        # Use Photovoltaik test
        sp = self.sp

        # Image names should not trigger a wrong message
        result = sp.spellcheck_blacklist(getTestCasePhotovolataik(), {'deuschland' : 'wrong'})
        assert len(result) == 0
        # Quoted text should not trigger a wrong message
        result = sp.spellcheck_blacklist(getTestCasePhotovolataik(), {'parity' : 'wrong'})
        assert len(result) == 0
        result = sp.spellcheck_blacklist(getTestCasePhotovolataik(), {'grid' : 'wrong'})
        assert len(result) == 0
        result = sp.spellcheck_blacklist(getTestCasePhotovolataik(), {'solarstrom' : 'wrong'})
        assert len(result) == 1
        result = sp.spellcheck_blacklist(getTestCasePhotovolataik(), {'stromnetz' : 'wrong'})
        assert len(result) == 1

    def test_spellcheck_blacklist_2(self):

        sp = self.sp

        result = sp.spellcheck_blacklist(getTestCasePietismus(), {'studirt' : 'wrong'})
        assert len(result) == 0
        result = sp.spellcheck_blacklist(getTestCasePietismus(), {'joachim' : 'wrong'})
        assert len(result) == 1
        result = sp.spellcheck_blacklist(getTestCasePietismus(), {u'göring' : 'wrong'})
        assert len(result) == 1

    def test_spellcheck_blacklist_3(self):

        sp = self.sp

        result = sp.spellcheck_blacklist(getTestCaseDogville(), {'wasington' : 'wrong'})
        assert len(result) == 0
        result = sp.spellcheck_blacklist(getTestCaseDogville(), {'manderlay' : 'wrong'})
        assert len(result) == 0

        result = sp.spellcheck_blacklist(getTestCaseDogville(), {'dogville' : 'wrong'})
        # We only find 1 result 
        assert len(result) == 1
        assert result[0][2] == 602

        result = sp.spellcheck_blacklist(getTestCaseDogville(), {'schwedischen' : 'wrong'})
        assert len(result) == 1
        result = sp.spellcheck_blacklist(getTestCaseDogville(), {'hobbyschriftsteller' : 'wrong'})
        assert len(result) == 1

        result = sp.spellcheck_blacklist(getTestCaseDogville(), {'gangstern' : 'wrong'})
        # We expect to find 2 results
        assert len(result) == 2
        assert result[0][2] == 1012
        assert result[1][2] == 1063
        assert getTestCaseDogville()[1012:1012+9] == "Gangstern"

    def test_spellcheck_blacklist_4(self):

        sp = self.sp

        # There should be zero results when protected by <!-- sic --> 
        result = sp.spellcheck_blacklist(getTestCaseKarel1(), {'visioen' : 'wrong'})
        assert len(result) == 0

        # There should be one results when not protected
        result = sp.spellcheck_blacklist(getTestCaseKarel2(), {'visioen' : 'wrong'})
        assert len(result) == 1
        assert result[0][2] == 61
        assert getTestCaseKarel2()[61:61+7] == "Visioen"

        # There should be zero results when protected by <!-- sic --> 
        result = sp.spellcheck_blacklist(getTestCaseKarel3(), {'visioen' : 'wrong'})
        assert len(result) == 0

        subtext = u' St\xe4dte ====\n- m\xe4nnliche '
        result = sp.spellcheck_blacklist(subtext, {'liche' : 'wrong'})
        assert len(result) == 0

    def test_zz_spellcheck_blacklist_detail(self):

        text = u"testtext with mistake&nbsp;and more words"
        assert len(self.sp.spellcheck_blacklist(text, {'mistake' : 'wrong'})) == 1
        assert len(self.sp.spellcheck_blacklist(text, {'more' : 'wrong'})) == 1

        # Hyphen is currently not escaped
        text = u"testtext with mistake&hyphen;and more words"
        assert len(self.sp.spellcheck_blacklist(text, {'mistake' : 'wrong'})) == 0
        assert len(self.sp.spellcheck_blacklist(text, {'more' : 'wrong'})) == 1

        text = u"testtext with mistake–and more words"
        assert len(self.sp.spellcheck_blacklist(text, {'mistake' : 'wrong'})) == 1
        assert len(self.sp.spellcheck_blacklist(text, {'more' : 'wrong'})) == 1

        # Something following a nowiki break should not be interpreted
        text = u"testtext with <nowiki></nowiki>mistake–and more words"
        assert len(self.sp.spellcheck_blacklist(text, {'mistake' : 'wrong'})) == 0
        assert len(self.sp.spellcheck_blacklist(text, {'more' : 'wrong'})) == 1

        text = u"testtext with ''mistake'' and more words"
        assert len(self.sp.spellcheck_blacklist(text, {'mistake' : 'wrong'})) == 0
        assert len(self.sp.spellcheck_blacklist(text, {'more' : 'wrong'})) == 1

        # Abbreviations end with a dot and the next word is not capitalized
        text = u"testtext with mistake. and more words"
        assert len(self.sp.spellcheck_blacklist(text, {'mistake' : 'wrong'})) == 0
        assert len(self.sp.spellcheck_blacklist(text, {'more' : 'wrong'})) == 1
        text = u"testtext with mistake. And more words"
        assert len(self.sp.spellcheck_blacklist(text, {'mistake' : 'wrong'})) == 1
        assert len(self.sp.spellcheck_blacklist(text, {'more' : 'wrong'})) == 1
        text = u"testtext with mistake.</ref> And more words"
        assert len(self.sp.spellcheck_blacklist(text, {'mistake' : 'wrong'})) == 1
        assert len(self.sp.spellcheck_blacklist(text, {'more' : 'wrong'})) == 1

        # Words that end with special endings
        text = u"testtext with mistake- and more words"
        assert len(self.sp.spellcheck_blacklist(text, {'mistake' : 'wrong'})) == 0
        assert len(self.sp.spellcheck_blacklist(text, {'more' : 'wrong'})) == 1

        # Words that end with upper case characters in the middle or that are too small
        text = u"testtext with mistAke and more words"
        assert len(self.sp.spellcheck_blacklist(text, {'mistake' : 'wrong'})) == 0
        assert len(self.sp.spellcheck_blacklist(text, {'more' : 'wrong'})) == 1
        text = u"testtext with Mistake and more words"
        assert len(self.sp.spellcheck_blacklist(text, {'mistake' : 'wrong'})) == 1
        assert len(self.sp.spellcheck_blacklist(text, {'more' : 'wrong'})) == 1
        text = u"testtext with Mi and more words"
        assert len(self.sp.spellcheck_blacklist(text, {'mi' : 'wrong'})) == 0
        text = u"testtext with Mis and more words"
        assert len(self.sp.spellcheck_blacklist(text, {'mis' : 'wrong'})) == 1
        assert len(self.sp.spellcheck_blacklist(text, {'more' : 'wrong'})) == 1

        # Words that are part of a wikilink 
        text = u"testtext with [[link]]mistake and more words"
        assert len(self.sp.spellcheck_blacklist(text, {'mistake' : 'wrong'})) == 0
        assert len(self.sp.spellcheck_blacklist(text, {'more' : 'wrong'})) == 1

if __name__ == "__main__":
    unittest.main()
