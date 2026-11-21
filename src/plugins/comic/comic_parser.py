import feedparser
import html
import re
COMICS ={
"XKCD":{
"feed":"https://xkcd.com/atom.xml",
"element":lambda feed :feed .entries [0 ].description ,
"url":lambda element :re .search (r'<img[^>]+src=["\"]([^"\"]+)["\"]',element ).group (1 ),
"title":lambda feed :feed .entries [0 ].title ,
"caption":lambda element :re .search (r'<img[^>]+alt=["\"]([^"\"]+)["\"]',element ).group (1 ),
},
"Цианид и счастье":{
"feed":"https://explosm-1311.appspot.com/",
"element":lambda feed :feed .entries [0 ].description ,
"url":lambda element :re .search (r'<img[^>]+src=["\"]([^"\"]+)["\"]',element ).group (1 ),
"title":lambda feed :feed .entries [0 ].title .split (" - ")[1 ].strip (),
"caption":lambda element :"",
},
"Субботний утренний завтрак, хлопья":{
"feed":"http://www.smbc-comics.com/comic/rss",
"element":lambda feed :feed .entries [0 ].description ,
"url":lambda element :re .search (r'<img[^>]+src=["\"]([^"\"]+)["\"]',element ).group (1 ),
"title":lambda feed :feed .entries [0 ].title .split ("-")[1 ].strip (),
"caption":lambda element :re .search (r'Hovertext:<br />(.*?)</p>',element ).group (1 ),
},
"Библейское сообщество Перри":{
"feed":"https://pbfcomics.com/feed/",
"element":lambda feed :feed .entries [0 ].description ,
"url":lambda element :re .search (r'<img[^>]+src=["\"]([^"\"]+)["\"]',element ).group (1 ),
"title":lambda feed :feed .entries [0 ].title ,
"caption":lambda element :re .search (r'<img[^>]+alt=["\"]([^"\"]+)["\"]',element ).group (1 ),
},
"Сомнительный контент":{
"feed":"http://www.questionablecontent.net/QCRSS.xml",
"element":lambda feed :feed .entries [0 ].description ,
"url":lambda element :re .search (r'<img[^>]+src=["\"]([^"\"]+)["\"]',element ).group (1 ),
"title":lambda feed :feed .entries [0 ].title ,
"caption":lambda element :"",
},
"Плохо прорисованные линии":{
"feed":"https://poorlydrawnlines.com/feed/",
"element":lambda feed :feed .entries [0 ].get ('content',[{}])[0 ].get ('value',''),
"url":lambda element :re .search (r'<img[^>]+src=["\"]([^"\"]+)["\"]',element ).group (1 ),
"title":lambda feed :feed .entries [0 ].title ,
"caption":lambda element :"",
},
"Комиксы о динозаврах":{
"feed":"https://www.qwantz.com/rssfeed.php",
"element":lambda feed :feed .entries [0 ].description ,
"url":lambda element :re .search (r'<img[^>]+src=["\"]([^"\"]+)["\"]',element ).group (1 ),
"title":lambda feed :feed .entries [0 ].title ,
"caption":lambda element :re .search (r'title="(.*?)" />',element .replace ('\n','')).group (1 ),
},
"название веб-комикса":{
"feed":"https://webcomicname.com/rss",
"element":lambda feed :feed .entries [0 ].description ,
"url":lambda element :re .search (r'<img[^>]+src=["\"]([^"\"]+)["\"]',element ).group (1 ),
"title":lambda feed :"",
"caption":lambda element :"",
},
}
def get_panel (comic_name ):
    feed =feedparser .parse (COMICS [comic_name ]["feed"])
    try :
        element =COMICS [comic_name ]["element"](feed )
    except IndexError :
        raise RuntimeError ("Не удалось получить последний комикс.")
    return {
    "image_url":COMICS [comic_name ]["url"](element ),
    "title":html .unescape (COMICS [comic_name ]["title"](feed )),
    "caption":html .unescape (COMICS [comic_name ]["caption"](element )),
    }