from urllib import parse
from urllib import robotparser
from lxml import html
import requests
from multiprocessing import Pool
import io
from PIL import Image

AGENT_NAME = "sebbot"
URL_BASE = "https://boards.4channel.org/"
parser = robotparser.RobotFileParser()
parser.set_url(parse.urljoin(URL_BASE, 'robots.txt'))
parser.read()

def get_tree(url):
    if parser.can_fetch('sebbot', url):
        result = requests.get(url)
        return html.document_fromstring(result.content)
    else:
        raise "4Chan's robot.txt disallows this"


def is_transparent(image):
    width, height = image.size

    widths = [int(width / i) - 1 for i in range(1,10)] + [0]
    heights = [int(height / i) - 1 for i in range(1,10)] + [0]

    for x in [0, width - 1]:
        for y in heights:
            if image.getpixel((x, y))[3] != 255:
                return True
    for y in [0, height - 1]:
        for x in widths:
            if image.getpixel((x, y))[3] != 255:
                return True
    return False


def process_image(image):
    data = requests.get(image).content
    data_bytes = io.BytesIO(data)
    img = Image.open(data_bytes)
    if img.mode in ["P", "RGBA"]:
        if is_transparent(img.convert('RGBA')):
            name = image.split("/")[-1]
            print("saving " + name)
            img.save("img/" + name)


def process_thread(thread):
    links = get_tree(thread).xpath('//a[@class="fileThumb"]')
    images = ['https:' + e.get('href') for e in links]
    for image in images:
        if image.endswith((".gif", ".png")):
            process_image(image)


def process_page(page):
    links = get_tree(page).xpath('//a[@class="replylink"]')
    threads = [parse.urljoin(URL_BASE, 'a/' + thread.get("href")) for thread in links if len(thread.get("href")) != 16]
    print(page + " had threads: " + str(len(threads)))
    for thread in threads:
        process_thread(thread)


pages = [parse.urljoin(URL_BASE, 'a/' + (str(i) if i != 1 else "")) for i in range(1, 10)]
with Pool(len(pages)) as p:
    p.map(process_page, pages)

