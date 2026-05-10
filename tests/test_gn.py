from newspaper.google_news import GoogleNewsSource
import newspaper

config = newspaper.Config()
source = GoogleNewsSource(country="US", period="1d", max_results=5)
source.build(keyword="MU stock news")
for a in source.articles[:5]:
    print(a.title)
