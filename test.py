import re
from optparse import OptionParser
from datetime import datetime
import codecs
from BeautifulSoup import BeautifulSoup
import urllib

class Participant(object):
    def __init__(self, name, style, link, description, votes):
        self.name = name
        self.style = style
        self.link = link
        self.description = description
        self.votes = votes

    def __str__(self):
        return self.pprint()

    def __repr__(self):
        return self.pprint()

    def pprint(self):
        return u"%s, %s (%s) - %d" % (self.name,
                                      self.style,
                                      self.link,
                                      self.votes)

class FetchParticipantException(Exception):
    def __init__(self, url):
        self.url = url
    def __str__(self):
        return u"Could not parse participant by %s" % self.url

class PageProcessor(object):
    def __init__(self, url, filename):
        self.url = url
        self.filename = filename
        self.pages = self.gen_pages()

    def gen_pages(self):
        pages = []
        for i in range(0, 12):
            pages.append(self._gen_next_page(self.url, i))
        return pages

    def _gen_next_page(self, url, i):
        return u"%s?start=%d" % (url, 12*i)

    def parse_participant(self, url):
        str_data = urllib.urlopen(url).read()
        data = str_data.decode('utf-8')
        soup = BeautifulSoup(data)
        partic_info = soup.find("div", "u4asn-1")
        if partic_info is None:
            raise FetchParticipantException(url)
        info = partic_info.find("div", "u4a-desc")
        results = [x.text for x in (info.h3, info.span, info.p) if x is not None]
        name = results[0]
        style = results[1]
        descr = results[2] if len(results) > 2 else u""
        votes = int(soup.find("div", "u4asn-2").find("div", "total").text)
        soup.close()
        return Participant(name=name,
                        link=url,
                        style=style,
                        description=descr,
                        votes=votes)

    # returns an unsorted list of participants
    def parse_page(self, url):
        f = urllib.urlopen(url)
        if f.getcode() != 200:
            print "Could not fetch participants page %s!" % url
            raise FetchParticipantException(url)
        soup = BeautifulSoup(f)
        links = map(lambda tag: tag.a.get("href"), soup.findAll("div", "news"));
        participants = []
        for link in links:
            try:
                parsed_p = self.parse_participant(link)
                participants.append(parsed_p)
            except FetchParticipantException:
                continue
        soup.close()
        return participants

    def process(self):
        all_participants = []
        for page_url in self.pages:
            try:
                page_results = self.parse_page(page_url)
                all_participants = all_participants + page_results
            except FetchParticipantException as fpe:
                print "Something went wrong while processing page %s : " % \
                (page_url, fpe.strerror)
        return all_participants

    def save_results(self, participants):
        # sort results first
        p_sorted = sorted(participants, key=lambda x: x.votes, reverse=True)
        f = codecs.open(self.filename, 'w', encoding="utf-8")
        for p in p_sorted:
            save_format = u"%d %s \n" % (p_sorted.index(p) + 1, p.pprint())
            f.write(save_format)
        f.close()

    def run(self):
        results = self.process()
        self.save_results(results)

def main():
    # parse command line options
    p = re.compile('[:.\s]')
    curr_datetime = str(datetime.now())
    default_filename = "rivals_%s.txt" % p.sub('-',curr_datetime)
    parser = OptionParser()
    parser.add_option("-u", "--url")
    parser.add_option("-f", "--file", default=default_filename)
    (options, args) = parser.parse_args()
    processor = PageProcessor(url=options.url, filename=options.file)
    processor.run()

if __name__ == "__main__":
    main()

