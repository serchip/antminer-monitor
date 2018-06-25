#-*- coding:utf-8 -*-
from flask import (jsonify,
                   render_template,
                   request,
                   redirect,
                   url_for,
                   flash,
                   )
from lib.pycgminer import (get_summary,
                               get_pools,
                               get_stats,
                               )
from lib.util_hashrate import update_unit_and_value
from sqlalchemy.exc import IntegrityError
from app import application, db, logger, __version__
from app.models import Miner, MinerModel, Settings, MinerСontainer
import re
from datetime import timedelta
import time


@application.route('/', methods=['GET'])
def miners():
    # Init variables
    start = time.clock()
    container_id = request.args.get('c', 1)
    miners = Miner.query.all()
    if container_id:
        miners = Miner.query.filter_by(container_id=container_id)
    models = MinerModel.query.all()
    containers = MinerСontainer.query.all()
    active_miners = []
    inactive_miners = []
    workers = {}
    miner_chips = {}
    temperatures = {}
    fans = {}
    hash_rates = {}
    hw_error_rates = {}
    uptimes = {}
    total_hash_rate_per_model = {"L3+": {"value": 0, "unit": "MH/s" },
                                "S7": {"value": 0, "unit": "GH/s" },
                                "S9": {"value": 0, "unit": "GH/s" },
                                "D3": {"value": 0, "unit": "MH/s" },
                                "T9": {"value": 0, "unit": "TH/s" },
                                "A3": {"value": 0, "unit": "GH/s" },
                                "L3": {"value": 0, "unit": "MH/s" },
                                "R4": {"value": 0, "unit": "TH/s" },
                                "V9": {"value": 0, "unit": "TH/s" },}
                                
    errors = False
    miner_errors = {}

    for miner in miners:
        miner_stats = miner.get_stats()
        # if miner not accessible
        if miner_stats['STATUS'][0]['STATUS'] == 'error':
            errors = True
            inactive_miners.append(miner)
        else:
            # Get worker name
            miner_pools = miner.get_pools()
            try:
                worker = miner_pools['POOLS'][0]['User']
            except KeyError:
                worker = 'None'
            # Get miner's ASIC chips
            asic_chains = [miner_stats['STATS'][1][chain] for chain in miner_stats['STATS'][1].keys() if
                           "chain_acs" in chain]
            # count number of working chips
            O = [str(o).count('o') for o in asic_chains]
            Os = sum(O)
            # count number of defective chips
            X = [str(x).count('x') for x in asic_chains]
            Xs = sum(X)
            # get number of in-active chips
            _dash_chips = [str(x).count('-') for x in asic_chains]
            _dash_chips = sum(_dash_chips)
            # Get total number of chips according to miner's model
            # convert miner.model.chips to int list and sum
            chips_list = [int(y) for y in str(miner.model.chips).split(',')]
            total_chips = sum(chips_list)
            # Get the temperatures of the miner according to miner's model
            temps = [int(miner_stats['STATS'][1][temp]) for temp in
                     sorted(miner_stats['STATS'][1].keys(), key=lambda x: str(x)) if
                     re.search(miner.model.temp_keys + '[0-9]', temp) if miner_stats['STATS'][1][temp] != 0]
            # Get fan speeds
            fan_speeds = [miner_stats['STATS'][1][fan] for fan in
                          sorted(miner_stats['STATS'][1].keys(), key=lambda x: str(x)) if
                          re.search("fan" + '[0-9]', fan) if miner_stats['STATS'][1][fan] != 0]
            # Get GH/S 5s
            ghs5s = float(str(miner_stats['STATS'][1]['GHS 5s']))
            # Get HW Errors
            hw_error_rate = miner_stats['STATS'][1]['Device Hardware%']
            # Get uptime
            uptime = timedelta(seconds=miner_stats['STATS'][1]['Elapsed'])
            #
            workers.update({miner.ip: worker})
            miner_chips.update({miner.ip: {'status': {'Os': Os, 'Xs': Xs, '-': _dash_chips},
                                           'total': total_chips,
                                           }
                                })
            temperatures.update({miner.ip: temps})
            fans.update({miner.ip: {"speeds": fan_speeds}})
            value, unit = update_unit_and_value(ghs5s, total_hash_rate_per_model[miner.model.model]['unit'])
            hash_rates.update({miner.ip: "{:3.2f} {}".format(value, unit)})
            hw_error_rates.update({miner.ip: hw_error_rate})
            uptimes.update({miner.ip: uptime})
            total_hash_rate_per_model[miner.model.model]["value"] += ghs5s
            active_miners.append(miner)

            # Flash error messages
            if Xs > 0:
                error_message = "[WARNING] '{}' chips are defective on miner '{}'.".format(Xs, miner.ip)
                logger.warning(error_message)
                flash(error_message, "warning")
                errors = True
                miner_errors.update({miner.ip: error_message})
            if Os + Xs < total_chips:
                error_message = "[ERROR] ASIC chips are missing from miner '{}'. Your Antminer '{}' has '{}/{} chips'." \
                    .format(miner.ip,
                            miner.model.model,
                            Os + Xs,
                            total_chips)
                logger.error(error_message)
                flash(error_message, "error")
                errors = True
                miner_errors.update({miner.ip: error_message})
#            if temps:
#                if max(temps) >= 80:
#                    error_message = "[WARNING] High temperatures on miner '{}'.".format(miner.ip)
#                    logger.warning(error_message)
#                    flash(error_message, "warning")
#
#                if not temps:
#                    temperatures.update({miner.ip: 0})
#                    error_message = "[ERROR] Could not retrieve temperatures from miner '{}'.".format(miner.ip)
#                    logger.warning(error_message)
#                    flash(error_message, "error")

    # Flash success/info message
    if not miners:
        error_message = "[INFO] No miners added yet. Please add miners using the above form."
        logger.info(error_message)
        flash(error_message, "info")
    elif not errors:
        error_message = "[INFO] All miners are operating normal. No errors found."
        logger.info(error_message)
        flash(error_message, "info")

    # flash("[INFO] Check chips on your miner", "info")
    # flash("[SUCCESS] Miner added successfully", "success")
    # flash("[WARNING] Check temperatures on your miner", "warning")
    # flash("[ERROR] Check board(s) on your miner", "error")

    # Convert the total_hash_rate_per_model into a data structure that the template can
    # consume.
    total_hash_rate_per_model_temp = {}
    for key in total_hash_rate_per_model:
        value, unit = update_unit_and_value(total_hash_rate_per_model[key]["value"], total_hash_rate_per_model[key]["unit"])
        if value > 0:
            total_hash_rate_per_model_temp[key] = "{:3.2f} {}".format(value, unit)


    end = time.clock()
    loading_time = end - start
    return render_template('home.html',
                           version=__version__,
                           models=models,
                           containers=containers,
                           container_id=int(container_id),
                           active_miners=active_miners,
                           inactive_miners=inactive_miners,
                           workers=workers,
                           miner_chips=miner_chips,
                           temperatures=temperatures,
                           fans=fans,
                           hash_rates=hash_rates,
                           hw_error_rates=hw_error_rates,
                           uptimes=uptimes,
                           total_hash_rate_per_model=total_hash_rate_per_model_temp,
                           loading_time=loading_time,
                           miner_errors=miner_errors,
                           )


@application.route('/add', methods=['POST'])
def add_miner():
    miner_ip = request.form['ip']
    miner_model_id = request.form.get('model_id')
    miner_remarks = request.form['remarks']
    container_id = request.form['container_id']

    # exists = Miner.query.filter_by(ip="").first()
    # if exists:
    #    return "IP Address already added"

    try:
        miner = Miner(ip=miner_ip, model_id=miner_model_id, container_id=container_id, remarks=miner_remarks)
        db.session.add(miner)
        db.session.commit()
        flash("Miner with IP Address {} added successfully".format(miner.ip), "success")
    except IntegrityError as e:
        db.session.rollback()
        flash("IP Address {} already added".format(miner_ip), "error")

    try:
        miner.check_stats()
    except TypeError:
        pass
    return redirect(url_for('miners'))


@application.route('/delete/<id>')
def delete_miner(id):
    miner = Miner.query.filter_by(id=int(id)).first()
    db.session.delete(miner)
    db.session.commit()
    return redirect(url_for('miners'))


@application.route('/refresh/<id>')
def refresh_miner(id):
    import os
    miner = Miner.query.filter_by(id=int(id)).first()
    if miner.model_id == 3:
        os.system('ssh root@%s "/etc/init.d/bmminer.sh restart > /dev/null 2>&1"' % miner.ip)
    else:
        os.system('ssh root@%s "/etc/init.d/cgminer.sh restart > /dev/null 2>&1"' % miner.ip)
    return redirect(url_for('miners'))


@application.route('/reset/<id>')
def reset_miner(id):
    import os
    miner = Miner.query.filter_by(id=int(id)).first()
    os.system('ssh root@%s "/sbin/reboot"' % miner.ip)
    return redirect(url_for('miners'))