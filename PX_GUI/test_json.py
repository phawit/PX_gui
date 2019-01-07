import json
import datetime
import time

# def UpdateJSON(key, value):
date_str = datetime.datetime.now().strftime("%Y%m%d")
date_time_str = datetime.datetime.now().strftime("%Y%m%d-%H:%M:%S")
print(date_time_str)
history_data = {}

sold_item = {
            "7640129890101": 5,
            "8850006332146": 6,
            "8852086001028": 6,
            "8858393000136": 6
        }

sold_price = {
            "7640129890101": 40.00,
            "8850006332146": 20.00,
            "8852086001028": 30.00,
            "8858393000136": 50.00
        }

sold_item2 = {
            "7640129890101": 1
        }

# if date_str in history_data:
#     pass
# else:
#     history_data[date_str] = {}

history_data[date_time_str] = {}
history_data[date_time_str]['Total Price'] = 800
history_data[date_time_str]['Price'] = sold_price
history_data[date_time_str]['Items'] = sold_item
# time.sleep(3)
# date_time_str = datetime.datetime.now().strftime("%Y%m%d-%H:%M:%S")
# history_data[date_str][date_time_str] = sold_item2

with open('history/'+date_str + '.json', 'w') as fp:
    json.dump(history_data, fp, sort_keys=True, indent=4, separators=(',', ': '))


    # for k, v in template_json.iteritems():
    #     old_key = k
    # template_json[date_str] = template_json.pop(old_key)
    # date_data[unicode(date_str, "utf-8")] = template_json.pop(date_str)

# if key == 'sell':
#     date_data[date_str][u'Daily Sales'] += value[2]
#     if value[0] in date_data[date_str][u'Item Sales']:
#         date_data[date_str][u'Item Sales'][value[0]] = value[1] + date_data[date_str][u'Item Sales'][value[0]]
#     else:
#         date_data[date_str][u'Item Sales'][value[0]] = value[1]
# elif key == 'stock':
#     if value[0] in date_data[date_str][u'Stock Adding']:
#         date_data[date_str][u'Stock Adding'][value[0]] = value[1] + date_data[date_str][u'Stock Adding'][value[0]]
#     else:
#         date_data[date_str][u'Stock Adding'][value[0]] = value[1]

# for item in items_list:
#     date_data[date_str][u'Current Stock'][unicode(item['Barcode'], "utf-8")] = int(item['Stock'])

# with open('history.json', 'w') as fp:
#     json.dump(date_data, fp, sort_keys=True, indent=4, separators=(',', ': '))
