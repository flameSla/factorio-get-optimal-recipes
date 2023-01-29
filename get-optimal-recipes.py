import json
from typing import Any
from fractions import Fraction
import sys

packs_names_to_depth = {}

# ====================================
par_debugging = False


def debug(*args):
    global par_debugging
    if par_debugging:
        # print(*args, file=sys.stderr, flush=True)
        print(*args, flush=True)


# ====================================
# добавлен метод add
class dict_bp(dict):
    def __add__(self, other):
        temp = dict_bp(self)
        for key, value in other.items():
            if key in temp:
                temp[key] += value
            else:
                temp[key] = value
        return temp

    def __iadd__(self, other):
        for key, value in other.items():
            if key in self:
                self[key] += value
            else:
                self[key] = value
        return self

    def __str__(self):
        s = str("\n")
        for k, v in self.items():
            s += '\t"{}" = {}\n'.format(k, v)
        return s


# ====================================
def get_recipes(file_name: str) -> Any:
    # json_all - содержимое json файла
    # packs_names_to_depth -> перечень пакетов науки
    # {'automation-science-pack': 0, 'logistic-science-pack': 1, ... }
    global par_debugging
    par_debugging = True

    # read json file
    with open(file_name, "r") as f:
        json_all = json.load(f)

    for i, tech in enumerate(json_all["technologies"]):
        # if "angelsore9-crystal-processing" in tech["recipes"]:
        debug()
        debug("==================")
        debug("tech = ", type(tech), tech)
        if i == 2:
            break

    par_debugging = False
    debug()
    debug("==================")
    debug("packs")
    packs_temp = []
    for tech in json_all["technologies"]:
        if "science-pack" in tech["name"]:
            debug()
            debug("==================")
            debug("tech = ", type(tech), tech)
            debug()
            packs_temp.append(tech)

    debug("++++++++++++++++++++")
    packs_names_to_depth = {}
    for t in sorted(packs_temp, key=lambda a: len(a["research_unit_ingredients"])):
        depth = len(t["research_unit_ingredients"])
        if depth == 1:
            pack = t["research_unit_ingredients"][0]["name"]
            packs_names_to_depth[pack] = 0
        pack = t["name"]
        packs_names_to_depth[pack] = depth
        debug("t = ", len(t["research_unit_ingredients"]), type(t), t)
        debug("---------------------")

    return packs_names_to_depth, json_all


# ====================================
def get_allowed_recipes(pack_name):
    # получить список рецептов, которые доступны на текущем уровне технологий
    global packs_names_to_depth
    global json_all

    global par_debugging
    par_debugging = False

    depth = packs_names_to_depth[pack_name]

    packs = set()
    for pack in [k for k, v in packs_names_to_depth.items() if v <= depth]:
        packs.add(pack)
    debug("packs = ", type(packs), packs)

    techs = [t for t in json_all["technologies"] if t["recipes"]]
    techs_recipes = set()
    for t in techs:
        techs_recipes.update(t["recipes"])

    recipes = [
        r["name"]
        for r in json_all["recipes"]
        if r["name"] not in techs_recipes and r["enabled"] == True
    ]

    techs_recipes = {}
    for t in techs:
        s = set([a["name"] for a in t["research_unit_ingredients"]])
        for r in t["recipes"]:
            techs_recipes[r] = s

    for r in json_all["recipes"]:
        if (
            r["name"] in techs_recipes
            and r["enabled"] == True
            and techs_recipes[r["name"]] <= packs
        ):
            recipes.append(r["name"])

    debug("len(recipes) = ", type(len(recipes)), len(recipes))
    debug(
        'len(json_all["recipes"]) = ',
        type(len(json_all["recipes"])),
        len(json_all["recipes"]),
    )

    return recipes


# ====================================
def debug_flows(flows):
    global par_debugging
    if par_debugging:
        print_flows(flows)


def print_flows(flows):
    print("flows:")
    for f in flows:
        print("\t", end="")
        for k, v in f.items():
            print("'{}' = {} ".format(k, v), end="")
        print()
    print()


# ====================================
def get_flow(id, amount):
    global json_all
    global recipes_name_to_id

    k = Fraction(1)

    res = dict_bp()
    recipe = json_all["recipes"][id]

    k_products = Fraction(recipe["products"][0]["amount"])
    for p in recipe["products"]:
        if p["amount"] > k_products:
            k_products = Fraction(p["amount"])
    if amount < 0:
        res[recipe["products"][0]["name"]] = amount
        amount *= -1
    for i in recipe["ingredients"]:
        res[i["name"]] = amount / k / k_products

    return res


def is_balance(flows, completely_balanced: bool, final_ingredients):
    # print()
    # print('\tfinal_ingredients = ', type(final_ingredients), final_ingredients)
    # print()
    temp = dict_bp()
    for f in flows:
        temp += f
    if completely_balanced:
        res = [
            {i: temp[i]}
            for i in temp.keys()
            if temp[i] != 0 and i not in final_ingredients
        ]
    else:
        global recipes_name_to_id
        res = [
            {i: temp[i]}
            for i in temp.keys()
            if temp[i] != 0
            and i not in final_ingredients
            and len(recipes_name_to_id[i]) == 1
        ]
    return len(res) == 0, res


def get_all_ingredients(*, items: dict(), final_ingredients=()):
    global par_debugging
    par_debugging = False

    global json_all
    global recipes_name_to_id
    res = dict_bp()

    k = Fraction(1)
    # if item_name in productivity:
    #     k = productivity[item_name]
    # else:
    #     k = Fraction(1)
    #     debug("'{}': Fraction(1.0),".format(item_name))
    flows = []
    for item_name, amount in items.items():
        if item_name in recipes_name_to_id:
            ids = recipes_name_to_id[item_name]
            debug("ids = ", type(ids), ids)
            if len(ids) == 1:
                debug(
                    'json_all["recipes"][ids[0]] = ',
                    type(json_all["recipes"][ids[0]]),
                    json_all["recipes"][ids[0]],
                )
                flow = get_flow(ids[0], amount)
                debug("")
                debug(flow)
                flows.append(flow)
            else:
                assert len(ids) == 1
                debug("len(ids) > 1")
                debug("ids = ", type(ids), ids)

    debug("")
    debug("flows = ", type(flows), flows)
    res = recursion_get_all_ingredients(flows, final_ingredients)
    debug()
    debug("==================")
    debug("get_all_ingredients")
    debug("res = ", type(res), res)

    return {item_name: amount}, res


def recursion_get_all_ingredients(flows, final_ingredients):
    res = dict_bp()
    global par_debugging
    par_debugging = False

    debug()
    debug("==================")
    debug("recurcive")
    debug("flows = ", type(flows), flows)

    balanced, unbalanced_flows = is_balance(flows, False, final_ingredients)
    debug("balanced = ", type(balanced), balanced)
    debug("unbalanced_flows = ", type(unbalanced_flows), unbalanced_flows)
    if balanced:
        return is_balance(flows, True, final_ingredients), flows
    else:
        for f in unbalanced_flows:
            assert len(f) == 1
            for name, amount in f.items():
                # есть дубликаты?
                names = []
                for f in flows:
                    names.extend([k for k, v in f.items() if v < 0])
                if name in names:
                    debug()
                    debug("==================")
                    debug(" удалить дубликаты ")
                    debug("name = ", type(name), name)
                    debug("names = ", type(names), names)
                    debug_flows(flows)
                    run = True
                    while run:
                        run = False
                        for i, f in enumerate(flows):
                            if name in f and f[name] < 0:
                                # нашли дубликат
                                amount -= f[name]
                                del flows[i]
                                run = True
                                break

                    debug_flows(flows)

                ids = recipes_name_to_id[name]
                assert len(ids) == 1
                flow = get_flow(ids[0], -amount)
                debug("flow = ", type(flow), flow)
                flows.append(flow)
                debug("flows = ", type(flows), flows)

        res = recursion_get_all_ingredients(flows, final_ingredients)
        return res


######################################
#
# main
if __name__ == "__main__":

    packs_names_to_depth, json_all = get_recipes("BobAngelBio.json")

    par_debugging = True
    debug()
    debug("==================")
    debug("packs")
    debug(packs_names_to_depth)
    debug()
    debug(packs_names_to_depth.keys())
    par_debugging = False

    # print()
    # print("==================")
    # print("recipes_name_to_id")

    recipes_name_to_id = {}
    for id, r in enumerate(json_all["recipes"]):
        for p in r["products"]:
            if p["name"] not in recipes_name_to_id:
                recipes_name_to_id[p["name"]] = []
            recipes_name_to_id[p["name"]].append(id)

    par_debugging = False
    for k in recipes_name_to_id.keys():
        debug(
            k,
            "recipes_name_to_id[k] = ",
            type(recipes_name_to_id[k]),
            recipes_name_to_id[k],
        )

    print(" ++++++++++++ ")
    # res = get_all_ingredients(item_name="automation-science-pack", amount=1)
    name, (is_balance, flows) = get_all_ingredients(
        items={
            "automation-science-pack": 1,
            # "logistic-science-pack": 1,
        },
        final_ingredients=["coal"],
    )
    print("name = ", type(name), name)
    print("is_balance = ", type(is_balance), is_balance)
    print("flows = ")
    for f in flows:
        print("\t", end="")
        for k, v in f.items():
            print('"{}" = {}  '.format(k, v), end="")
        print()

    print()
    print("==================")
    print("get_allowed_recipes(pack_name)")
    # 'automation-science-pack', 'logistic-science-pack', 'chemical-science-pack', 'military-science-pack', 'advanced-logistic-science-pack', 'production-science-pack', 'utility-science-pack', 'space-science-pack'
    allowed_recipes = get_allowed_recipes("automation-science-pack")
