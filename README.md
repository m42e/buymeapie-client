# Buy Me A Pie Client

A Simple minimal client that makes use of the Web API. 

It currently supports:

- get lists
- get list items
- create list
- delete list
- add items
- mark items as purchased
- delete items
- change amount of items
- add unique items
- change unique items group


So basic functionality is there.


## Example

````python

import buymeapie
bap = buymeapie.BuyMeAPie(username=user, password=pass_)
print(bap.lists)
print(bap.lists[0].not_purchased)
bap.lists[0].add_item('Onions', 10)
print(bap.lists[0].not_purchased)

```
