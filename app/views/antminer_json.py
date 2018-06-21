from flask import jsonify
from app import application
from lib.pycgminer import (get_summary,
                               get_pools,
                               get_stats,
                               )


@application.route('/<ip>/summary')
def summary(ip):
    output = get_summary(ip)
    return jsonify(output)


@application.route('/<ip>/pools')
def pools(ip):
    output = get_pools(ip)
    return jsonify(output)


@application.route('/<ip>/stats')
def stats(ip):
    output = get_stats(ip)
    return jsonify(output)