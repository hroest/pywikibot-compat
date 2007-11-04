# -*- coding: utf-8 -*-
#!/usr/bin/python

import wikipedia, editarticle
"""
Script to remove links that are being or have been spammed.
Usage:

spamremove.py spammedsite.com

It will use Special:Linksearch to find the pages on the wiki that link to
that site, then for each page make a proposed change consisting of removing
all the lines where that url occurs. You can choose to:
* accept the changes as proposed
* edit the page yourself to remove the offending link
* not change the page in question

Command line options:
* -automatic: Do not ask, but remove the lines automatically. Be very careful
              in using this option!

"""
__version__ = '$Id$'

def main():
    automatic = False
    msg = {
        'de': u'Entferne in Spam-Blacklist eingetragenen Weblink auf %s',
        'en': u'Removing links to spammed site %s',
        'nl': u'Links naar gespamde site: %s verwijderd',
        'pt': u'Removendo links de spam do site %s',
    }
    spamSite = ''
    for arg in wikipedia.handleArgs():
        if arg.startswith("-automatic"):
            automatic = True
        else:
            spamSite = arg
    if not automatic:
        wikipedia.put_throttle.setDelay(1)
    if not spamSite:
        wikipedia.output(u"No spam site specified.")
        sys.exit()
    mysite = wikipedia.getSite()
    pages = list(set(mysite.linksearch(spamSite)))
    wikipedia.getall(mysite, pages)
    for p in pages:
        text = p.get()
        if not spamSite in text:
            continue
        # Show the title of the page we're working on.
        # Highlight the title in purple.
        wikipedia.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<" % p.title())
        lines = text.split('\n')
        newpage = []
        lastok = ""
        for line in lines:
            if spamSite in line:
                if lastok:
                    wikipedia.output(lastok)
                wikipedia.output('\03{lightred}%s\03{default}' % line)
                lastok = None
            else:
                newpage.append(line)
                if line.strip():
                    if lastok is None:
                        wikipedia.output(line)
                    lastok = line
        if automatic:
            answer = "y"
        else:
            answer = wikipedia.inputChoice(u'\nDelete the red lines?',  ['yes', 'no', 'edit'], ['y', 'N', 'e'], 'n')
        if answer == "n":
            continue
        elif answer == "e":
            editor = editarticle.TextEditor()
            newtext = editor.edit(text, highlight = spamSite, jumpIndex = text.find(spamSite))
        else:
            newtext = "\n".join(newpage)
        if newtext != text:
            p.put(newtext, wikipedia.translate(mysite, msg) % spamSite)

try:
    main()
finally:
   wikipedia.stopme()
