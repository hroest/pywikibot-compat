#!/usr/bin/python
# -*- coding: utf-8  -*-

"""Unit test for blacklist spellchecker
"""

import wikipedia as pywikibot
from spellcheck_wordlist import BlacklistSpellchecker
import textrange_parser 

import unittest

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
        1964 ''Kleine Vlaamse Suite''
        Heroisch Visioen
        Rustige Zomeravond
        """

def getTestCaseKarel3():
    """ This test checks that specifically wrongly spelled names are not corrected

    mypage = pywikibot.Page(pywikibot.getSite(), 'Karel De Schrijver')
    text = mypage.getOldVersion(55865499)
    """

    return u"""
        1964 ''Kleine Vlaamse Suite''
        Heroisch Visioen<!-- sic! -->
        Rustige Zomeravond
        """

def getTestCaseKarel4():
    """ This test checks that specifically wrongly spelled names are not corrected

    mypage = pywikibot.Page(pywikibot.getSite(), 'Karel De Schrijver')
    text = mypage.getOldVersion(55865499)
    """

    return u"""
        * 1964 ''Kleine Vlaamse Suite''
        *# Heroisch Visioen
        *# Rustige Zomeravond
        """

def getTestCaseSchilcher():
    return u"""
        {{Dieser Artikel|behandelt den österreichischen Rotwein. Für Personen gleichen Namens siehe [[Schilcher (Begriffsklärung)]].}}
        {{Widerspruch|Artikel|[[Blauer Wildbacher]]|Disk=Diskussion:Schilcher}}

        [[Datei:Glas Schilcher.jpg|mini|hochkant|Schilcher im Glas]]

        '''Schilcher''', selten auch ''Schiller'', ist die Bezeichnung des Weins aus einer [[Weinbau in Österreich|österreichischen]] [[Rotwein]]traubensorte.<ref name=schil>[http://www.oesterreichwein.at/unser-wein/oesterreichs-rebsorten/rotwein/blauer-wildbacher/ Beschreibung der Rebsorte].</ref> Er wird als [[Roséwein]]<ref name=schil/><ref>[http://www.ris.bka.gv.at/Dokumente/BgblAuth/BGBLA_2011_II_111/BGBLA_2011_II_111.pdf Weinbezeichnungsverordnung], österreichisches Bundesgesetzblatt Teil II Nr. 111/2011: § 1 Abs. 2 Z 10 lit. a.</ref> in der [[Steiermark]] aus der [[Liste von Rebsorten|roten Rebsorte]] [[Blauer Wildbacher]] gewonnen und hat einen geschützten Handelsnamen: Schilcher muss aus der Steiermark kommen. Im Frühstadium seiner Gärung wird der Wein als '''Schilchersturm''' angeboten.
        """

def getTestCaseFrieden():
    return u"""ussion unterscheidet man zwischen dem oben genannten ''engen Friedensbegriff''(„''[[negativer Frieden]]''“), der die Abwesenheit von [[Konflikt]]en beinhaltet, und einem ''weiter gefassten Friedensbegriff'' („''[[positiver Frieden]]''“). Letzterer umfasst neben dem Fehlen kriegerischer Gewalt, bei """

# ##########################################################################
# Start of Test
class SpellcheckBlacklistTestCase(unittest.TestCase):

    def setUp(self):
        self.sp = BlacklistSpellchecker()

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
        res = self.sp.forbiddenRanges(text, removeNested=False)
        assert len(res) == 3
        assert res[0] == [0,18]
        assert res[1] == [50,87]
        assert res[2] == [24,107]
        assert text[18:24] + text[107:] == " TEXT  MORE TEXT"
        #
        res = self.sp.forbiddenRanges(text, removeNested=True)
        assert len(res) == 2
        assert res[0] == [0,18]
        assert res[1] == [24,107]

        # Nested
        text = "{{test template }} TEXT {{test2 param1 = [[test|test2]] }} MORE TEXT \"some quoted\" TEXT <!-- some comment --> FINAL"
        res = self.sp.forbiddenRanges(text, removeNested=False)
        assert len(res) == 5
        assert res == [[0, 18], [24, 58], [41, 55], [69, 82], [88, 109]]
        #
        res = self.sp.forbiddenRanges(text)
        assert len(res) == 4
        assert res == [[0, 18], [24, 58], [69, 82], [88, 109]]

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
        assert result[0][2] == 56
        assert getTestCaseKarel2()[56:56+7] == "Visioen"

        # There should be zero results when protected by <!-- sic --> 
        result = sp.spellcheck_blacklist(getTestCaseKarel3(), {'visioen' : 'wrong'})
        assert len(result) == 0

    def test_spellcheck_blacklist_5(self):

        sp = self.sp

        result = sp.spellcheck_blacklist(getTestCaseSchilcher(), {'schil' : 'wrong'})
        assert len(result) == 0

        result = sp.spellcheck_blacklist(getTestCaseSchilcher(), {'weins' : 'wrong'})
        assert len(result) == 1

    def test_spellcheck_blacklist_6(self):

        sp = self.sp

        result = sp.spellcheck_blacklist(getTestCaseFrieden(), {'mfasst' : 'wrong'})
        assert len(result) == 0

        result = sp.spellcheck_blacklist(getTestCaseFrieden(), {'positiver' : 'wrong'})
        assert len(result) == 0

    def test_spellcheck_blacklist_detail(self):
        text = u"testtext with mistake&nbsp;and more words"
        assert len(self.sp.spellcheck_blacklist(text, {'mistake' : 'wrong'})) == 1
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

        # Words that start with '''
        text = u"testtext with '''A'''mistake and more words"
        assert len(self.sp.spellcheck_blacklist(text, {'mistake' : 'wrong'})) == 0
        assert len(self.sp.spellcheck_blacklist(text, {'more' : 'wrong'})) == 1

        # Words that end with upper case characters in the middle or that are too small
        text = u"testtext with mistAke and more words"
        assert len(self.sp.spellcheck_blacklist(text, {'mistake' : 'wrong'})) == 0
        assert len(self.sp.spellcheck_blacklist(text, {'more' : 'wrong'})) == 1
        text = u"testtext with Mistake and more words"
        assert len(self.sp.spellcheck_blacklist(text, {'mistake' : 'wrong'})) == 1
        assert len(self.sp.spellcheck_blacklist(text, {'more' : 'wrong'})) == 1
        text = u"testtext with Mis and more words"
        assert len(self.sp.spellcheck_blacklist(text, {'mis' : 'wrong'})) == 1
        assert len(self.sp.spellcheck_blacklist(text, {'more' : 'wrong'})) == 1

        # Words that are part of a wikilink 
        text = u"testtext with [[link]]mistake and more words"
        assert len(self.sp.spellcheck_blacklist(text, {'mistake' : 'wrong'})) == 0
        assert len(self.sp.spellcheck_blacklist(text, {'more' : 'wrong'})) == 1

        # TODO Hamisfeld -> poem : why doesnt it work? 
        text = u"testtext <poem>with mistake and</poem> more words"
        assert len(self.sp.spellcheck_blacklist(text, {'mistake' : 'wrong'})) == 0
        assert len(self.sp.spellcheck_blacklist(text, {'more' : 'wrong'})) == 1

        text = u"some text <!--sic-->''“). Drei Gelübde legt der Benediktinermönch im Laufe seines Ordenslebens ab: " 
        assert len(self.sp.spellcheck_blacklist(text, {'aufe' : 'wrong'})) == 0
        assert len(self.sp.spellcheck_blacklist(text, {'seines' : 'wrong'})) == 1

        text = u"""Manz setzt nochmals beim Scheitern der ''Dienstagsgespräche'' ein und erhebt gegenüber den Zürcher Pfarrherrn den Vorwurf, sie hätten bei den Unterredungen ihre Position nicht mit Bibel begründet: ''Sy haben wol ir meinung herfürbracht, doch nicht mit geschrifften gegründt''.<ref>Leonhard von Muralt / Walter Schmid (Hrsg.), a.a.O., Nr. 24, S. 3f</ref> Auch sei ihnen, den Gegnern der Kindertaufe, nicht genügend Zeit eingeräumt worden, ihre Auffassungen darzustellen."""
        assert len(self.sp.spellcheck_blacklist(text, {u'gegründt' : 'wrong'})) == 0

        text = u""" Ein Barpianist unterscheidet sich wesentlich von anderen Pianisten (Klassik, Jazz, Boogie usw.), da er niemals auf Bühne im Vordergrund konzertant agiert. Die klassische Grundausbildung ist für diese Spieltechnik Grundvoraussetzung. Eine besondere Herausforderung besteht in der Interpretation der rhythmischen Vielfalt. Mit der linken Hand spielt man Schlagzeug und Bass, mit der rechten Hand die Gesangs- oder Saxophonmelodie, und die Mittelstimmen imitieren Gitarren- oder Percussionsklänge, die bei Latins unverzichtbar sind. <ref>''Das professionelle BARPIANO Studium'' Zum Erlernen des professionellen Spielen von Barmusik am Klavier. BARMUSIK RECORDS, ISBN 978-3-200-03144-9</ref>Das umfangreiche Repertoire besteht aus allen Bereichen der Musik aus allen Ländern der Welt (Pop, Jazzstandards, Oper, Operette, Wienerlieder, Latins usw.). Ein Feingefühl die Atmosphäre durch die richtige Wahl des Repertoire der Stimmung anzupassen und die am besten geeignete Interpretationsart (Im Vortrag, Rhythmisch...) zu wählen, zeichnen einen guten Barpianisten aus. Die Fähigkeit Sänger auch begleiten zu können wird erwartet. 
        """
        assert len(self.sp.spellcheck_blacklist(text, {u'Repertoir' : 'wrong'})) == 0

    def test_spellcheck_blacklist_slow(self):

        mypage = pywikibot.Page(pywikibot.getSite(), 'Unterschrift')
        text = mypage.getOldVersion(128568384)
        assert len(self.sp.spellcheck_blacklist(text, {u'olg' : 'wrong'})) == 0

        mypage = pywikibot.Page(pywikibot.getSite(), 'Regen')
        text = mypage.get()
        assert len(self.sp.spellcheck_blacklist(text, {u'urch' : 'wrong'})) == 0

        mypage = pywikibot.Page(pywikibot.getSite(), 'Cottbus')
        text = mypage.get()
        assert len(self.sp.spellcheck_blacklist(text, {u'stadhalle' : 'wrong'})) == 0

if __name__ == "__main__":
    unittest.main()
