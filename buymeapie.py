import requests
import requests.exceptions

_BASE_URL = "https://app.buymeapie.com"


class ProductGroup(object):
    """Group Colors"""
    __COLORS = [
        "b4bec6",
        "524dcf",
        "864f9e",
        "ba2e38",
        "e57542",
        "ff5699",
        "75b35a",
        "26b0c7",
        "c1c12f",
        "20a881",
        "8faecd",
        "416362",
        "f4b72f",
        "a19080",
        "931f54",
        "4cc9f5",
        "ff2966",
        "c4b8ce",
        "9e5e59",
        "4f3c6d",
        "5372c5",
        "a85271",
        "f57f03",
        "957d41",
        "4f99aa",
        "fd9c69",
        "de2b17",
        "797d88",
        "b4cc8b",
    ]

    @classmethod
    def color(cls, color_id: int):
        if color_id < len(cls.__COLORS):
            return cls.__COLORS[color_id]
        return cls.__COLORS[0]


class BuyMeAPie(object):
    """BuyMeAPie Client"""
    def __init__(self, *, username, password, autologin=True, base_url=_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Origin': 'https://app.buymeapie.com', 'Accept': 'appliaction/json, text/plain, */*', 'User-Agent':	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Safari/605.1.15'})
        self.session.auth = (username, password)
        if autologin:
            self.login()
        self.refresh_all()

    def _url(self, endpoint):
        return f"{self.base_url}/{endpoint}"

    def _request(self, method, endpoint, *args, **kwargs):
        resp = self.session.request(method, self._url(endpoint), *args, **kwargs)
        if resp.status_code != 200:
            print(self._url(endpoint))
            print(f"Got respone status {resp.status_code}.")
            print(f"Text: {resp.text}")
            print(args, kwargs)
        try:
            return resp.json()
        except requests.exceptions.JSONDecodeError as e:
            print("Could not parse JSON for", self._url(endpoint))
            raise e
        return resp

    def _get(self, endpoint, *args, **kwargs):
        return self._request("get", endpoint, *args, **kwargs)

    def _put(self, endpoint, *args, **kwargs):
        return self._request("put", endpoint, *args, **kwargs)

    def _post(self, endpoint, *args, **kwargs):
        return self._request("post", endpoint, *args, **kwargs)

    def _delete(self, endpoint, *args, **kwargs):
        return self._request("delete", endpoint, *args, **kwargs)

    def login(self):
        r = self._get("bauth")
        self.accountinfo = r

    def refresh_all(self):
        self._lists = None
        self._restrictions = None
        self._unique_items = None
        self._unique_items_dict = None

    def clear_cache(self):
        self._put("clear_cache")

    @property
    def premium(self):
        return self.restrictions["premium"]

    @property
    def premium_expiration(self):
        return self.restrictions["premium_expiration_timestamp"]

    @property
    def max_lists(self):
        return self.restrictions["maxListsCount"]

    @property
    def restrictions(self):
        if self._restrictions is None:
            self._restrictions = self._get("restrictions")
        return self._restrictions

    @property
    def lists(self):
        if self._lists is None:
            r = self._get("lists")
            self._lists = list(map(lambda x: List(self, x), r))
        return self._lists

    @property
    def unique_items(self):
        if self._unique_items is None:
            self._unique_items = list(
                map(lambda x: UniqueItem(self, x), self._get("unique_items"))
            )
        return self._unique_items

    def get_unique(self, name, group_id=0):
        if self._unique_items_dict is None:
            self._unique_items_dict = {i.name: i for i in self.unique_items}

        if name not in self._unique_items_dict:
            r = self._put(
                f"unique_items/{name}", json={"group_id": group_id, "use_count": 1}
            )
            self._unique_items_dict[name] = UniqueItem(self, r)
            self._unique_items.append(self._unique_items_dict[name])
        return self._unique_items_dict[name]

    def create_list(self, name):
        result = self._post(
            "lists", json={"items_not_purchased": 0, "items_purchased": 0, "name": name}
        )
        return List(self, result)

    def create_item(self, name: str, group_id: int):
        result = self._put(
            f"unique_items/{name}",
            json={"group_id": group_id, "permanent": False, "use_count": 0},
        )
        return UniqueItem(self, result)


class List(object):
    def __init__(self, buymeapie: BuyMeAPie, info: dict):
        self._bap = buymeapie
        self._info = info
        self._items = None

    @property
    def name(self):
        return self._info["name"]

    @property
    def id(self):
        return self._info["id"]

    @property
    def rename(self, name):
        new_info = self._bap._put(
            f"lists/{self.id}", json={"emails": self._info["emails"], "name": name}
        )
        self._info = new_info
        self._bap.refresh_all()
        return self

    @property
    def changed(self, till: int):
        changed_items = self._bap._get(f"lists/{self.id}/changed_items/{till}")
        changed_items = list(map(lambda x: Item(self._bap, self, x), changed_items))

    @property
    def items(self):
        if self._items is None:
            items = self._bap._get(f"lists/{self.id}/items")
            self._items = list(map(lambda x: Item(self._bap, self, x), items))
        return self._items

    @property
    def not_purchased(self):
        return list(filter(lambda x: not x.purchased, self.items))

    def add_item(self, name, amount):
        self._bap.get_unique(name).update_use()
        response = self._bap._post(
            f"lists/{self.id}/items",
            json={
                "amount": str(amount),
                "is_purchased": False,
                "title": name,
            },
        )
        item = Item(self._bap, self, response)
        self._items.append(item)
        return item

    def delete(self):
        self._bap._delete(f"lists/{self.id}")
        self._info = None

    def __repr__(self):
        return f"{self.name} ({self.id})"

    def __str__(self):
        return self.__repr__()


class Item(object):
    def __init__(self, buymeapie: BuyMeAPie, list: List, info: dict):
        self._bap = buymeapie
        self._list = list
        self._info = info

    @property
    def id(self):
        return self._info["id"]

    @property
    def name(self):
        return self._info["title"]

    @property
    def amount(self):
        return self._info["amount"]
    @amount.setter
    def amount(self, val):
        self._info["amount"] = val
        self._update()

    @property
    def purchased(self):
        return self._info["is_purchased"] or self._info['deleted']

    def purchase(self):
        self._info["is_purchased"] = True
        self._update()

    def _update(self):
        self._info = self._bap._put(
            f"lists/{self._list.id}/items/{self.id}",
            json={
                "is_purchased": True,
                "title": self.name,
                "amount": self.amount,
            },
        )

    def delete(self):
        self._bap._delete(f"lists/{self._list.id}/items/{self.id}")
        self._list._items.remove(self)

    def __repr__(self):
        if self.amount != "":
            return f"{self.name}: {self.amount}"
        else:
            return f"{self.name}"

    def __str__(self):
        return self.__repr__()


class UniqueItem(object):
    def __init__(self, buymeapie: BuyMeAPie, info: dict):
        self._bap = buymeapie
        self._info = info

    @property
    def name(self):
        return self._info["title"]

    @property
    def use_count(self):
        return self._info["use_count"]

    @property
    def last_use(self):
        return self._info["last_use"]

    @property
    def group_id(self):
        return self._info["group_id"]

    @property
    def amount(self):
        return self._info["amount"]

    def update_use(self):
        self._info["use_count"] += 1
        self._update()

    @group_id.setter
    def group_id(self, val):
        self._info["group_id"] = group_id
        self._update()

    def _update(self):
        self._bap.put(
            f"unique_items/{self.name}",
            json={
                "use_count": self.use_count,
                "permanent": self._info["permanent"],
                "group_id": self.group_id,
            },
        )

    def __repr__(self):
        return f"{self.name} ({self.group_id})"

    def __str__(self):
        return self.__repr__()
