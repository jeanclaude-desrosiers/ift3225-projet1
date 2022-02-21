from copy import copy
from typing import Any, Dict, List
from bs4 import BeautifulSoup
import sys
import random
import bs4

#####################
##### Constants #####
#####################

OUT_DIR = sys.argv[2]

with open("./template/index.html") as FP:
    QUESTION_TEMPLATE_BS = BeautifulSoup(FP, features="html.parser")

with open("./template/index-solution.html") as FP:
    SOLUTION_TEMPLATE_BS = BeautifulSoup(FP, features="html.parser")

HTML_FILENAME_ARR = [html_filename for html_filename in sys.argv[1].split(";") if html_filename.strip() != ""]

###########################
##### Obscure Section #####
###########################

LOREM_IPSUM = """
Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod
tempor incididunt ut labore et dolore magna aliqua. Mattis ullamcorper
velit sed ullamcorper morbi. Sem et tortor consequat id porta nibh
venenatis cras. Est pellentesque elit ullamcorper dignissim cras. Ultricies
tristique nulla aliquet enim tortor. Vitae et leo duis ut diam quam. Eget
mauris pharetra et ultrices neque. Sit amet porttitor eget dolor. Aenean et
tortor at risus viverra adipiscing at. Scelerisque eu ultrices vitae auctor eu
augue ut. Vehicula ipsum a arcu cursus vitae congue mauris rhoncus
aenean. Diam volutpat commodo sed egestas egestas fringilla phasellus
faucibus. Tellus mauris a diam maecenas sed enim ut sem. Sed risus
pretium quam vulputate dignissim suspendisse in. Porttitor lacus luctus
accumsan tortor posuere.
""".split()

LOREM_IPSUM_START_IDX = [idx for idx, word in enumerate(
    LOREM_IPSUM) if word[0].isupper()]


def get_lorem_ipsum(n: int) -> List[str]:
    start = LOREM_IPSUM_START_IDX[random.randrange(
        0, len(LOREM_IPSUM_START_IDX))]
    result = []  # type: List[str]

    for i in range(n):
        result.append(LOREM_IPSUM[(start + i) % len(LOREM_IPSUM)])

    return result


def obscure_text(text: str) -> str:
    text_len = len(text.split())

    return " ".join(get_lorem_ipsum(text_len))

def html_encode(src: str) -> str:
    without_lt = src.replace("<", "&lt;")
    without_gt = without_lt.replace(">", "&gt;")

    return without_gt

###########################
##### Extract Section #####
###########################


def extract_index_from_html(bs: BeautifulSoup) -> int:
    table = bs.find("table", class_="testDescription")

    second_row = table("tr")[1]  # type: bs4.Tag
    # this string ha the format "### of 172"
    count = second_row("td")[1].string  # type: str

    return int(count.split(" ")[0])


def extract_date_from_html(bs: BeautifulSoup) -> str:
    table = bs.find("table", class_="testDescription")

    fourth_row = table("tr")[3]  # type: bs4.Tag

    return fourth_row("td")[1].string  # type: str


def extract_revision_from_html(bs: BeautifulSoup) -> str:
    table = bs.find("table", class_="testDescription")

    fourth_row = table("tr")[3]  # type: bs4.Tag

    return fourth_row("td")[2].string  # type: str


def extract_title_from_html(bs: BeautifulSoup) -> str:
    return bs.find("title").string


def extract_link_from_html(bs: BeautifulSoup, rel: str) -> str:
    link = bs.find("link", rel=rel)

    if(link is None):
        return ""
    else:
        return link["href"]


def extract_test_from_html(bs: BeautifulSoup) -> List[bs4.Tag]:
    test_div = bs.find("div", class_="testText")

    return [child for child in test_div.children if isinstance(child, bs4.Tag)]


def extract_obscured_test_from_html(bs: BeautifulSoup) -> List[bs4.Tag]:
    test_div = copy(bs.find("div", class_="testText"))

    for descendant in test_div.descendants:
        if(descendant.string is not None):
            descendant.string = obscure_text(descendant.string)

    return [child for child in test_div.children if isinstance(child, bs4.Tag)]


def encode_from_tags(tags: List[bs4.Tag]) -> str:
    return "\n".join([tag.prettify() for tag in tags])


def extract_css_question_from_html(bs: BeautifulSoup) -> str:
    pass


def extract_from_html(html_filename: str) -> Dict[str, Any]:
    extracted = {}  # type: Dict[str, str | int | List[bs4.Tag]]

    with open(html_filename) as FP:
        bs = BeautifulSoup(FP, features="html.parser")

    with open(f"{html_filename}.css") as FP:
        css_content = "\n".join(FP.readlines())

    with open(f"{html_filename}.display.css") as FP:
        css_question = "\n".join(FP.readlines())

    extracted["title"] = extract_title_from_html(bs)
    extracted["index"] = extract_index_from_html(bs)
    extracted["date"] = extract_date_from_html(bs)
    extracted["revision"] = extract_revision_from_html(bs)
    extracted["prev"] = extract_link_from_html(bs, "prev")
    extracted["next"] = extract_link_from_html(bs, "next")
    extracted["solution"] = extract_test_from_html(bs)
    extracted["solution_encoded"] = encode_from_tags(extracted["solution"])
    extracted["question"] = extract_obscured_test_from_html(bs)
    extracted["question_encoded"] = encode_from_tags(extracted["question"])
    extracted["css"] = css_content
    extracted["css_question"] = css_question

    return extracted

##########################
##### Transf Section #####
##########################

# CSS are in OUT_DIR/css/###_solution.css
# HTML questions are in OUT_DIR/###_question.html
# HTML solutions are in OUT_DIR/###_solution.html


def transf_html(extracted: Dict[str, Any], template: BeautifulSoup):
    template.find("title").string = extracted["title"]
    template.find("header").find("h1").string = extracted["title"]

    index = extracted["index"]  # type: int
    template.find("header").find("nav").find(
        "p").string = f"Test {index} of 172"

    prev = template.find("a", rel="prev")
    if(index == 1):
        prev.name = "p"
        del prev["rel"]
        del prev["href"]
    else:
        prev["href"] = f"{index - 1}_question.html"

    next = template.find("a", rel="next")
    if(index == 172):
        next.name = "p"
        del next["rel"]
        del next["href"]
    else:
        next["href"] = f"{index + 1}_question.html"

    template.find("pre", id="css-question").string = extracted["css_question"]

    template.find("p", id="date-footer").string = extracted["date"]
    template.find("p", id="revision-footer").string = extracted["revision"]


def transf_question_html(extracted: Dict[str, Any],
                         template: BeautifulSoup) -> BeautifulSoup:
    transf_html(extracted, template)
    template.find(
        "pre", id="html-question").string = extracted["question_encoded"]

    template.find("div", id="html-result").clear()
    template.find("div", id="html-result").extend(extracted["question"])

    template.find("a", id="solution")[
        "href"] = f"{extracted['index']}_solution.html"

    return template


def transf_solution_html(extracted: Dict[str, Any],
                         template: BeautifulSoup,
                         out_dir: str = OUT_DIR) -> BeautifulSoup:
    transf_html(extracted, template)
    css_filename = f"css/{extracted['index']}_solution.css"

    with open(f"{out_dir}/{css_filename}", "w") as FP:
        FP.write(extracted["css"])

    template.find("link", id="css-solution")["href"] = css_filename

    template.find(
        "pre", id="html-question").string = extracted["solution_encoded"]

    template.find("div", id="html-result").clear()
    template.find("div", id="html-result").extend(extracted["solution"])

    template.find("a", id="question")[
        "href"] = f"{extracted['index']}_question.html"

    return template


########################
##### Main Section #####
########################

for html_filename in HTML_FILENAME_ARR:
    extracted = extract_from_html(html_filename)

    question_bs = transf_question_html(extracted, copy(QUESTION_TEMPLATE_BS))
    with open(f"{OUT_DIR}/{extracted['index']}_question.html", "w") as FP:
        FP.write(question_bs.prettify())

    solution_bs = transf_solution_html(extracted, copy(SOLUTION_TEMPLATE_BS))
    with open(f"{OUT_DIR}/{extracted['index']}_solution.html", "w") as FP:
        FP.write(solution_bs.prettify())
