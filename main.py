__author__ = 'jj'

import pandas
from scipy.spatial.distance import cosine
from scipy.stats import percentileofscore
from pprint import pprint
import itertools


import json, os
from bottle import route, run, request, response


PRODUCT_COLUMNS = [u'fit', u'size', u'color', u'type of clothing', u'brand', u'fabric', u'texture', u'price',
                   u'occasion', u'gender']
USER_COLUMNS = [u'geography', u'latino', u'age', u'income']
INPUT_DATA_FILENAME = 'hackathon_tab_delimited.txt'
INPUT_UNIQVALS_FILENAME = 'uniqVals.txt'


def is_match(row, _attributes):

    for k, v in _attributes.iteritems():
        if row[k] != v:
            return False

    return True


def get_self_popularity(_data, _attributes):

    # short-circuiting
    if len(_attributes) == 0:
        return 1

    totalCount = _data.shape[0]
    count = 0

    for _, row in _data.iterrows():

        if is_match(row, _attributes):
            count += 1

    score = 1. * count / totalCount
    # print 'Total count = %i, or %.2f' % (count, score)

    return score


def get_popularity_for_item(_data, _attributes):
    """
    popularity of an item
    :param _attributes: product attributes (size, color, etc)
    :return: a double in the range of 0~10
    """

    # short-circuiting
    if len(_attributes) == 0:
        return 1

    # based on the item's appearance itself
    selfScore = get_self_popularity(_data, _attributes)

    # linear combination of the popularity score of item's similar items
    relScores = 0

    # for _, row in _data.iterrows():
    #     simScore = compute_similarity(_attributes, row)
    #
    #     if simScore < 1.0:  # not the row itself
    #         rowsOwnAttrs = dict(row[_attributes])
    #         relRowScore = get_self_popularity(_data, rowsOwnAttrs)
    #         # print 'similarity: %.2f, relevant row score: %.2f' % (simScore, relRowScore)
    #         relScores += simScore * relRowScore

    res = selfScore + relScores/100.
    print '>>>> Self Score: %.2f, Rel Score: %.2f => %.2f' % (selfScore, relScores, res)
    return res

# TODO: make this better
def compute_similarity(attributes, row):
    """
    :param row: pandas series
    :return: a double
    """

    totalLen = len(attributes)
    count = 0

    for k, v in attributes.iteritems():
        if row[k] == v:
            count += 1

    return 1. * count / totalLen


def parse_uniq_vals_mapping():

    STR_2_VAL_MAP = {}

    for line in open(INPUT_UNIQVALS_FILENAME).readlines():
        rawK, rawVals = line.strip().split(':')
        k = rawK.strip()
        vals = [v.strip() for v in rawVals.strip().split(',')]

        STR_2_VAL_MAP[k] = vals

    return STR_2_VAL_MAP


def main(attributes):

    uniqValsMapping = parse_uniq_vals_mapping()

    data = pandas.read_table(INPUT_DATA_FILENAME)

    # productAttrs = data[PRODUCT_COLUMNS]
    # userAttrs = data[USER_COLUMNS]


    print '='*15
    thisScore = 0

    keys = attributes.keys()
    l = [uniqValsMapping[k] for k in keys]

    allScores = []
    for vs in itertools.product(*l):

        print vs
        d = dict(zip(keys, vs))
        s = get_popularity_for_item(data, d)
        allScores.append(s)

        if d == attributes:
            thisScore = s

    return percentileofscore(allScores, thisScore, 'weak')



def __get_json_from_request(_request):
    print type(_request)
    if _request.json is None:
        return _request.POST.dict
    else:
        return _request.json

# curl -H "Content-Type: application/json" -X GET -d '[1,5]' http://0.0.0.0:5000/rec_user
@route('/', method='POST')
def home():
    """
    input: attributes = {'fit': 'loose', 'type of clothing': 'sweater'}
    :return: a double
    """
    print 'In server. Data received:'

    try:
        requestJSONData = __get_json_from_request(request)
        pprint(requestJSONData)
        attributes = { k: v[0] for k, v in requestJSONData.iteritems()}

        output = main(attributes)

    except Exception as e:
        print 'ERROR encountered:', e.message
        output = []

    # not sure if this is needed
    response.add_header('Access-Control-Allow-Origin', '*')

    return json.dumps(output)


# if __name__ == '__main__':

# attributes = {'fit': 'loose',
#               'type of clothing': 'sweater'}
#
# print 'res = ', main(attributes)

run(host='localhost', port=os.environ.get('PORT', 5000))

print 'DONE.'