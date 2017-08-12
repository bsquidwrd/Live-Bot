import json
import sys
from django.core import serializers


def logify_object(obj):
    """
    Returns a JSON string containing usually a Queryset of items based on :attr:`obj`
    """
    return json.dumps(json.loads(serializers.serialize("json", obj)), sort_keys=True, indent=4)


def logify_dict(d):
    """
    Returns a JSON string containing the information within a :attr:`d`
    """
    return json.dumps(d, sort_keys=True, indent=4)


def logify_exception_info():
    """
    Returns a string with information about the last exception that was thrown.
    """
    return "Filename: {0.tb_frame.f_code.co_filename}\nLine: {0.tb_lineno}\n".format(sys.exc_info()[2])
