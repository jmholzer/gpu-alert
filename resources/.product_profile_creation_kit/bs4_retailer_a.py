import copy
import json

from bs4 import BeautifulSoup

with open("<retailer_a>.html", "r") as in_:
    content = in_.read()

soup = BeautifulSoup(content, "lxml")

results = soup.find_all("a", {"class": "productBox"})
names = (result.findChild("div", {"class": "product-name"}).text for result in results)


with open("product_template.json", "r") as in_:
    target = json.load(in_)

    new_products = dict()

    for i, name in enumerate(names):
        new_products["product" + str(i)] = copy.deepcopy(target["products"]["product0"])
        new_products["product" + str(i)]["name"] = name

target["products"] = new_products
with open("RTX-3080.json", "w") as out:
    json.dump(target, out, indent=4)
