from optparse import OptionParser
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
        return u"%s - %d" % (self.link,
                                  self.votes)

    def __repr__(self):
        return u"%s - %d" % (self.link,
                                  self.votes)

class FetchParticipantException(Exception):
    def __init__(self, url):
        self.url = url
    def __str__(self):
        return u"Could not parse participant by %s" % self.url

def main():
    # parse command line options
    parser = OptionParser()
    parser.add_option("-u", "--url")
    parser.add_option("-f", "--file", default="rivals.out")
    (options, args) = parser.parse_args()
    all_participants = []
    for i in range(0, 12):
        try:
          new_link = gen_next_link(options.url, i)
          all_participants = all_participants + parse_page(new_link)
        except FetchParticipantException:
            print "Something went wrong while processing page %s" % new_link
            continue
    save_results(options.file, all_participants);

def gen_next_link(url, i):
    return u"%s?start=%d" % (url, 12*(i+1))

# returns an unsorted list of participants
def parse_page(url):
    f = urllib.urlopen(url)
    if f.getcode() != 200:
        raise FetchParticipantException(url)
    soup = BeautifulSoup(f)
    links = map(lambda tag: tag.a.get("href"), soup.findAll("div", "news"));
    participants = map(parse_participant, links)
    soup.close()
    return participants

def parse_participant(url):
    data = urllib.urlopen(url).read()
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

def save_results(filename, participants):
    # sort results first
    p_sorted = sorted(participants, key=lambda x: x.votes, reverse=True)
    f = open(filename, 'w')
    for p in p_sorted:
        f.write(u"%r \n" % p)
    f.close()

if __name__ == "__main__":
    main()

