import urllib.request
import urllib.parse
from html.parser import HTMLParser

class DDGParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results = []
        self.in_snippet = False
        self.in_title = False
        self.current_title = ""
        self.current_snippet = ""
        self.current_url = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "a" and "result__snippet" in attrs_dict.get("class", ""):
            self.in_snippet = True
            href = attrs_dict.get("href", "")
            if "uddg=" in href:
                self.current_url = urllib.parse.unquote(href.split("uddg=")[1].split("&")[0])
        elif tag == "h2" and "result__title" in attrs_dict.get("class", ""):
            self.in_title = True

    def handle_data(self, data):
        if self.in_snippet:
            self.current_snippet += data
        elif self.in_title:
            self.current_title += data

    def handle_endtag(self, tag):
        if tag == "a" and self.in_snippet:
            self.in_snippet = False
            if self.current_snippet.strip():
                self.results.append({
                    "title": self.current_title.strip(),
                    "snippet": self.current_snippet.strip(),
                    "url": self.current_url
                })
            self.current_snippet = ""
            self.current_title = ""
        elif tag == "h2" and self.in_title:
            self.in_title = False

url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote("site:reddit.com meditation cushions")
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
with urllib.request.urlopen(req) as response:
    html = response.read().decode()

p = DDGParser()
p.feed(html)
for r in p.results:
    print(r)
