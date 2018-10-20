import scrapy
import re
import os
import glob
import hashlib
import norvig
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.contrib.loader import XPathItemLoader
from scrapy.http.request import Request
from scrapy.item import Item
from tutorial.items import ImageItem
import language_check
from urllib.parse import urlparse
from langdetect import detect 
import whois
from collections import Counter

sep = '\t'

f1 = open('data.txt','w')
global_wordLen = 0
global_wc = 0
my_dict = {}

def getDomainName(url):
    parsed_uri = urlparse(url)
    domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
    return domain

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(2 ** 20), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def hashImages():
    filenames = glob.glob("C:/Users/****/scrapy_projects/tutorial/full/*.jpg")
    f1.write("Image Hashes: ")
    f1.write("[")
    for filename in filenames:
        f1.write(md5(filename)+", ")
    f1.write("]"+sep)

def imagePreloading(links):
    countPreLoadedImages = 0
    with open(links,'r') as f:
        for line in f:
            if line.endswith(('.png\n','.jpg\n')):
                countPreLoadedImages = countPreLoadedImages + 1 
    # Number of preloaded images is:
    f1.write(str(countPreLoadedImages)+sep)

def checkGrammar(content):
    incorrect = 0 #Number of grammmatically incorrect sentences
    sentences = fetchSentences(content)
    tool = language_check.LanguageTool('en-US')
    for line in sentences:
        line = line.strip()
        if re.match(r'^\s*$', line):
            continue
        if (detect(line) != 'en'): 
            continue
        matches = tool.check(line)
        if language_check.correct(line, matches).strip() == line:
            continue
        incorrect = incorrect + 1
    # Number of grammatically incorrect sentences is:
    f1.write(str(incorrect)+sep)

def countWords(line):   
    words = line.split(' ')
    wc = 0
    global global_wc
    global_wc = 0
    global global_wordLen 
    global_wordLen = 0
    for word in words:
        wc = wc + 1
        global_wordLen = global_wordLen + len(word)
    global_wc = global_wc + wc
    return wc 

def wrongWords(line):
    words = line.split(' ')
    wrong = 0
    for word in words:
        word = re.sub(r'\W+', '', word) #Keeps only letters in the word
        word = word.lower() # First word in each sentence has upper case letters
        if norvig.correction(word) is not word:
            wrong = wrong + 1
    return wrong

def countRelAbsHttpsLinks(links): 
    relCount = 0
    absCount = 0
    httpsCount = 0 
    with open(links,'r') as f:
        for line in f:
            if re.match(r"https://",line):
                absCount = absCount + 1
                httpsCount = httpsCount + 1
            if re.match(r"http://",line):
                absCount = absCount + 1
            if re.match(r"//",line):
                relCount = relCount + 1
    # Number of absolute links is: 
    f1.write(str(absCount)+sep)
    # Number of relative links is: 
    f1.write(str(relCount)+sep)
    # Number of links with https is: 
    f1.write(str(httpsCount)+sep)


def countInOutLinks(links):
    inCount = 0
    outCount = 0
    dir_path = os.path.dirname(os.path.realpath(links)).split("\\")[-1]
    dir_path = dir_path.strip()
    with open(links,'r') as f:
        for line in f:
            fullDomain = getDomainName(line)
            domain = fullDomain.split("/")[-2]
            domain = domain.strip()
            #Empty string is possible
            if not domain:
                continue
            if domain == dir_path:
                inCount = inCount + 1
            else:
                outCount = outCount + 1

    # Number of links pointing to the same domain is:
    f1.write(str(inCount)+sep)
    # Number of links pointing to a different domain is:
    f1.write(str(outCount)+sep)

def fetchSentences(content): 
    with open(content, 'r') as myfile:
        data=myfile.read()
    return re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', data)

def countSlashes(links): 
    #Average number of slashes in each url of a page
    slashCount = 0
    urlCount = 0
    with open(links,'r') as f:
        for line in f:
            if(line.count('/') -2 > 0):
                urlCount = urlCount + 1
                slashCount = slashCount + line.count('/') - 2
    # Average number of slashes is: 
    if(urlCount==0):
        f1.write("NULL"+sep)
        return
    f1.write(str("%.2f" % (slashCount/urlCount))+sep)


def countSentences(content):
    wrongCount = 0
    awc = 0 #Average number of words in a sentence or avg sentence length 
    global sc #Number of sentences in a file
    sc = 0
    sentences = fetchSentences(content)
    for line in sentences:
        line = line.strip()
        if re.match(r'^\s*$', line):
            continue
        if (detect(line) != 'en'): 
            continue
        sc = sc + 1
        awc = awc + countWords(line)
        wrongCount = wrongCount + wrongWords(line)
    # Number of incorrectly spelt words is:
    f1.write(str(wrongCount)+sep)
    # Average sentence length is: 
    if(sc==0):
        f1.write("NULL"+sep)
        return
    f1.write(str("%.2f" % (awc/sc))+sep)

def extractLinks(links, response):
    with open(links,'w') as fi:
        one = response.xpath('//link/@href').extract()
        str1 = '\n'.join(one) # Convert list to a string to write to a file
        fi.write(str1)
        two = response.xpath('//a/@href').extract()
        str1 = '\n'.join(two)
        fi.write(str1)

def extractText(content, response):
    with open(content,'w') as fname:
        t = response.xpath('//h1/text()').extract()
        str1 = ' '.join(t)
        fname.write(str1)
        t = response.xpath('//h2/text()').extract()
        str1 = ' '.join(t)
        fname.write(str1)
        t = response.xpath('//p/text()').extract() 
        str1 = ' '.join(t)
        fname.write(str1)
        t = response.xpath('//h3/text()').extract()
        str1 = ' '.join(t)
        fname.write(str1)
        t = response.xpath('//div/text()').extract()
        str1 = ' '.join(t)
        fname.write(str1)
        t = response.xpath('//li/text()').extract()
        str1 = ' '.join(t)
        fname.write(str1)

class MySpider(CrawlSpider):
    name = 'MyCrawler'
    start_urls = [line.split('\t')[0].rstrip('\n') for line in open('urls.txt')]
    # Dictionary with fake and legit labels
    global my_dict
    my_dict = dict([(line.split('\t')[0].rstrip('\n'), line.split('\t')[1].rstrip('\n')) for line in open('urls.txt')])
    #f1.write('Domain\tPath\twhois_server\treferral_url\tUpdated on\tCreated on\texpiration_date\tname_servers\tstatus\temails\tdnssec\tname\torg\taddress\tcity\tstate\tzip_code\tcountry\t#AbsoluteLinks\t#RelativeLinks\t#HTTPSLinks\t#InLinks\t#OutLinks\tAvgSlashes\t#PreloadedImages\t#IncorrectlySpeltWords\tAvgSentenceLen\t#GrammaticallyIncorrectSentence\tAvgWordLen\t#WordsPerPage\tImageHashes\tlabel')
    rules =(Rule(LinkExtractor(allow = ()) ,callback = 'parse_item'),)  

    def parse_item(self, response):
        url_obj = urlparse(response.url)
        path = url_obj.path
        if path.endswith("/"):
            path = path[:-1]
        page = path.split("/")[-1]
        fullDomain = getDomainName(response.url) # with HTTP or HTTPS
        domain = fullDomain.split("/")[-2]
        newpath = r'C:\\Users\\****\\scrapy_projects\\tutorial\\' + domain
        if not os.path.exists(newpath):
            os.makedirs(newpath)
        os.chdir(newpath)
        filename = '%s.html' % (domain + " " + page)
        with open(filename, 'wb') as f:
            f.write(response.body)
        links = 'links-%s.txt' % (domain + " " + page)
        content = 'contents-%s.txt' % (domain + " " + page)
        f1.write("\n")
        f1.write(domain+sep)
        f1.write(page+sep)
        # 16 whois attributes
        f1.write(str(whois.whois(response.url).whois_server) +sep )
        f1.write(str(whois.whois(response.url).referral_url) +sep )
        f1.write(str(whois.whois(response.url).updated_date) +sep )
        f1.write(str(whois.whois(response.url).creation_date) +sep )
        f1.write(str(whois.whois(response.url).expiration_date) +sep )
        f1.write(str(whois.whois(response.url).name_servers) +sep )
        f1.write(str(whois.whois(response.url).status) +sep )
        f1.write(str(whois.whois(response.url).emails) +sep )
        f1.write(str(whois.whois(response.url).dnssec) +sep )
        f1.write(str(whois.whois(response.url).name) +sep )
        f1.write(str(whois.whois(response.url).org) +sep )
        f1.write(str(whois.whois(response.url).address) +sep )
        f1.write(str(whois.whois(response.url).city) +sep )
        f1.write(str(whois.whois(response.url).state) +sep )
        f1.write(str(whois.whois(response.url).zipcode) +sep )
        f1.write(str(whois.whois(response.url).country) +sep )
        
        extractLinks(links, response)
        countRelAbsHttpsLinks(links) 
        countInOutLinks(links)
        countSlashes(links)
        imagePreloading(links)

        extractText(content, response)
        countSentences(content)
        checkGrammar(content)

        # Average word length is: ??? global_wc can be zero
        f1.write(str("%.2f" % (global_wordLen/global_wc))+sep)
        # Number of words in the page:
        f1.write(str(global_wc)+sep)
        # Downloads images
        loader = XPathItemLoader(item = ImageItem(), response = response)
        loader.add_xpath('image_urls', '//img/@src')  
        hashImages() # Calculates hashes of images downloaded by scrapy
        # Write label into the data file 
        f1.write(my_dict.get(fullDomain,"redirect"))

        return loader.load_item()


        

