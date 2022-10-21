import yaml
import re

with open('config.yml', 'rb') as f:
    config = yaml.safe_load(f)

def check_input(range_strategy, size_strategy, size_param, size_amount, range1, range2):
    ret = ""
    if not re.search(r'^[\d\.]+$', size_amount):
        ret += "param 4 size_amount needs to be a number!\n"
    if not re.search(r'^[\d\.]+$', range1):
        ret += "param 5 range1 needs to be a number!\n"
    if not re.search(r'^[\d\.]+$', range2):
        ret += "param 6 range2 needs to be a number!\n"
    if not re.search(r'^\w+$', range_strategy):
        ret += "param 1 range_strategy needs to be a 'word' character!\n"
    if not re.search(r'^[a-zA-Z]+$', size_strategy):
        ret += "param 2 size_strategy needs to be a 'word' character!\n"
    if not re.search(r'^[a-zA-Z]+$', size_param):
        ret += "param 3 size_param needs to be a 'word' character!\n"
    return ret


def print_layers(layer_array, size_array):
    if len(layer_array) != len(size_array):
        raise ValueError("Length of layer/size arrays differ! Internal Error.")
    min_padding = config["round_to"]+1
    for lp in layer_array:
        if len(str(lp)) > min_padding:
            min_padding = len(str(lp))+1
    ret = "<pre>"
    for i in range(0, len(layer_array)):
        lp = str(layer_array[i])
        ret += "Layer "+str(i+1)+": " + lp
        for _ in range(0, min_padding-len(lp)):
            ret += " "
        ret += "- Size: " + str(size_array[i])+"\n"
    for _ in range(0, min_padding-1):
        ret += " "
    ret += "Total Order Size: "+str(sum(size_array))
    ret += "</pre>"
    return ret


def range_fib(first, last):
    span = first - last
    s1 = span*23.6/100
    s2 = span*38.2/100
    s3 = span*50/100
    s4 = span*61.8/100
    ret = [first]
    ret += [round((first-s1), config["round_to"])]
    ret += [round((first-s2), config["round_to"])]
    ret += [round((first-s3), config["round_to"])]
    ret += [round((first-s4), config["round_to"])]
    ret += [last]
    return ret


def range_even(first, last, layers):
    span = first - last
    part = round(span/layers, config["round_to"])
    ret = [first]
    for i in range(1, layers-1):
        ret += [round(first+(part*i), config["round_to"])]
    ret += [last]
    return ret


def size_even_startwith(layers, start_with):
    ret = [start_with]
    for _ in range(1, layers-1):
        ret += [start_with]
    ret += [sum(ret)*2]
    return ret


def size_even_maxtotal(layers, max_total):
    d = sum(size_even_startwith(layers, 1))
    n = round(max_total/d, 2)
    ret = size_even_startwith(layers, n)
    rem = max_total - sum(ret)
    ret[layers-1] = round(ret[layers-1] + rem, config["fiat_round_to"])
    return ret


def size_double_startwith(layers, start_with):
    ret = [start_with]
    for _ in range(1, layers):
        ret = ret + [round(sum(ret) * 2, config["fiat_round_to"])]
    return ret


def size_double_maxtotal(layers, max_total):
    d = sum(size_double_startwith(layers, 1))
    n = round(max_total/d, 2)
    ret = size_double_startwith(layers, n)
    rem = max_total - sum(ret)
    ret[layers-1] = round(ret[layers-1] + rem, config["fiat_round_to"])
    return ret


def layered(range_strategy, size_strategy, size_param, size_amount, range1, range2):
    input_val_msg = check_input(range_strategy, size_strategy, size_param, size_amount, range1, range2)
    if bool(input_val_msg):
        return input_val_msg
    range1 = float(range1)
    range2 = float(range2)
    size_amount = float(size_amount)

    if range_strategy == "fib":
        layers = 6
        larr = range_fib(range2, range1)
    elif range_strategy.startswith("even"):
        try:
            layers = int(range_strategy[-1])
            larr = range_even(range2, range1, layers)
        except:
            return "Unable to extract number of layers from: "+range_strategy
    else:
        return "range_strategy not supported: "+range_strategy

    if size_strategy == "double":
        if size_param == "startwith":
            sarr = size_double_startwith(layers, size_amount)
        elif size_param == "total":
            sarr = size_double_maxtotal(layers, size_amount)
        else:
            return "size_param not supported: "+size_param
    elif size_strategy == "even":
        if size_param == "startwith":
            sarr = size_even_startwith(layers, size_amount)
        elif size_param == "total":
            sarr = size_even_maxtotal(layers, size_amount)
        else:
            return "size_param not supported: "+size_param
    else:
        return "size_strategy not supported: "+size_strategy

    return print_layers(larr, sarr)
