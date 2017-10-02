"""
Copyright 2010 Brad Pitcher <bradpitcher@gmail.com>

    This file is part of python-eol.

    python-eol is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    python-eol is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with python-eol.  If not, see <http://www.gnu.org/licenses/>.
"""

import urllib, re
from xml.dom import minidom
from bs4 import BeautifulSoup

EXEMPLARS_URL = 'http://www.eol.org/exemplars.xml'
SEARCH_URL = 'http://www.eol.org/search.xml?q=%s'
PAGE_URL = 'http://eol.org/api/pages/1.0.xml?batch=false&id=%i&images_per_page=0&images_page=0&videos_per_page=0&videos_page=0&sounds_per_page=0&sounds_page=0&maps_per_page=0&maps_page=0&texts_per_page=5&texts_page=1&subjects=overview&licenses=all&details=true&common_names=true&synonyms=true&references=false&taxonomy=true&vetted=0&cache_ttl=&language=en'
#PAGE_URL = 'http://www.eol.org/api/pages/1.0.xml?id=%i&details=true'
IMAGES_URL = 'http://www.eol.org/pages/%i/images/%i.xml'
VIDEOS_URL = 'http://www.eol.org/pages/%i/videos/%i.xml'




def cleantext(input_text):
    _text = ''.join(e for e in input_text if e.isalnum() or e.isspace())
    _text = re.sub(r"\n", " ", _text)
    _text = _text.lower()
    return _text;





class eol:
    def __get_xml_doc(self, url):
        socket = urllib.urlopen(url)
        doc = minidom.parse(socket)
        socket.close()
        return doc

    def exemplars(self):
        return self.__get_xml_doc(EXEMPLARS_URL)

    def search(self, search_term):
        return self.__get_xml_doc(SEARCH_URL % search_term)

    def page(self, page_id):
        return self.__get_xml_doc(PAGE_URL % page_id)

    def images(self, page_id, page_num):
        return self.__get_xml_doc(IMAGES_URL % (page_id, page_num))

    def videos(self, page_id, page_num):
        return self.__get_xml_doc(VIDEOS_URL % (page_id, page_num))








