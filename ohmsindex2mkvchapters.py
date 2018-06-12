#!/usr/bin/env python
'''
ohms index 2 mkv chapters
converts index metadata from OHMS to XML for MKV chapters

TAG MAPPING
OHMS Index | MKV Chapter
point | ChapterAtom
title | ChapterString
time | ChapterTimeStart (x1Million)
language | ChapterLanguage (iso)
'''

import argparse
import datetime
from bs4 import BeautifulSoup
from pycountry import languages

class dotdict(dict):
	'''
    dot.notation access to dictionary attributes
    '''
	__getattr__ = dict.get
	__setattr__ = dict.__setitem__
	__delattr__ = dict.__delitem__

def make_mkv_edition(Chapters):
    '''
    makes the edition that the chapters are wrapped in
    '''
    soup = BeautifulSoup(features='xml')
    Edition = soup.new_tag('EditionEntry')
    Chapters.append(Edition)
    editionElements = [['FlagOrdered', 1], ['FlagHidden', 0], ['FlagDefault', 1], ['UID','']]
    for element in editionElements:
        if element[0] == 'UID':
            new_tag = soup.new_tag('Edition' + element[0])
            new_tag.string = str(1)
        else:
            new_tag = soup.new_tag('Edition' + element[0])
            new_tag.string = str(element[1])
        Edition.append(new_tag)
    return Edition

def make_mkv_chapter(chapters, chapterElements):
    '''
    takes chapters dictionary object and converts it to mkv chapters xml
    variables starting with Caps are XML
    variables lowercase or camelCase are dictionary
    '''
    soup = BeautifulSoup("<Chapters>", features = 'xml')
    Chapters = soup.Chapters
    Edition = make_mkv_edition(Chapters)
    for chapter in chapters:
        ChapterAtom = soup.new_tag("ChapterAtom")
        Edition.append(ChapterAtom)
        for element in chapterElements:
            new_tag = soup.new_tag('Chapter' + element)
            new_tag.string = str(chapter[element])
            ChapterAtom.append(new_tag)
        ChapterAtom = make_display(chapter, ChapterAtom, soup)
    return Chapters

def make_chapter_atom(point, ohmsIndex, args):
    '''
    make a single dictionary of of a chapter
    '''
    chapter = dotdict({})
    chapter.TimeStart = str(datetime.timedelta(seconds=int(point.time.string))) + ".000000000"
    if not chapter.TimeStart.startswith('00:'):
        chapter.TimeStart = "0" + chapter.TimeStart
    chapter.Display = []
    string = point.title.string
    languages = get_language(ohmsIndex, args)
    display = [string, languages.primary]
    chapter.Display.append(display)
    if point.title_alt.string:
        string = point.title_alt.string
        language = get_language(ohmsIndex, args)
        display = [string, languages.alt]
        chapter.Display.append(display)
    chapter.FlagHidden = 0
    chapter.FlagEnabled = 1
    return chapter

def make_display(chapter, ChapterAtom, soup):
    '''
    makes the soupy ChapterDisplay element
    '''
    for dis in chapter.Display:
        Display = soup.new_tag('ChapterDisplay')
        new_tag = soup.new_tag('ChapterString')
        new_tag.string = dis[0]
        Display.append(new_tag)
        new_tag = soup.new_tag('ChapterLanguage')
        new_tag.string = dis[1]
        Display.append(new_tag)
        ChapterAtom.append(Display)
    return ChapterAtom

def get_language(ohmsIndex, args):
    '''
    handler for some of the zanyness
    '''
    langsSorted = dotdict({'primary':'', 'alt':''})
    langsSortedIso = dotdict({'primary':'', 'alt':''})
    primary = ohmsIndex.language.string
    if ohmsIndex.transcript_alt_lang.string:
        alt = ohmsIndex.transcript_alt_lang.string
    else:
        langAlt = None
    if args.lang_alt_reverse:
        langsSorted.primary = alt
        langsSorted.alt = primary
    else:
        langsSorted.primary = primary
        langsSorted.alt = alt
    for key,lang in langsSorted.items():
        try:
            l = languages.get(name = lang)
            langsSortedIso[key] = l.alpha_3
        except:
            langsSortedIso[key] = 'und'
    return langsSortedIso

def make_chapters(ohmsIndex, args):
    '''
    create a list of chapters
    '''
    chapters = []
    chapterElements = ['UID', 'TimeStart', 'FlagHidden', 'FlagEnabled']
    points = ohmsIndex.find_all('point')
    count = 1
    for point in points:
        chapter = make_chapter_atom(point, ohmsIndex, args)
        chapter.UID = count
        count = count + 1
        chapters.append(chapter)
    return chapters, chapterElements

def write_mkv_chapters(Chapters, args):
    '''
    writes the output to a file
    '''
    outputfile = open(args.o, 'w+')
    outputfile.write(str(Chapters))
    outputfile.close
    return True

def init_ohms_index(args):
    '''
    grab the index xml file and make a soup from it
    '''
    with open(args.i.replace("\\","/"), 'r') as file:
        soup = BeautifulSoup(file, 'lxml')
    return soup

def init_args():
    '''
    grab arguments from the cli
    '''
    parser = argparse.ArgumentParser(description="Make an MKV Chapters xml file from an OHMS index xml file")
    parser.add_argument('-i', '--input', dest='i', help='the OHMS index xml file')
    parser.add_argument('-o', '--output', dest='o', help='output path for converted MKV XML file')
    parser.add_argument('--lang-alt-reverse', dest='lang_alt_reverse', action='store_true',
        default=False, help="reverses the lagnauge assignments between normal and _alt tags")
    args = parser.parse_args()
    if not args.o:
        args.o = args.i.replace('.xml','-MKV-Chapters.xml')
    return args

def main():
    '''
    do the thing
    '''
    args = init_args()
    ohmsIndex = init_ohms_index(args)
    chapters, chapterElements = make_chapters(ohmsIndex, args)
    Chapters = make_mkv_chapter(chapters, chapterElements)
    success = write_mkv_chapters(Chapters, args)

if __name__ == '__main__':
    main()
