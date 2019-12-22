"""Entry point to Zoyra."""
import json
import logging

from google.appengine.ext import deferred, ndb

from flask import Flask, request
from model.policymodel import PolicyModel
from model.schedulesmodel import SchedulesModel
from tasks import policy_tasks, schedule_tasks
from util import tz

API_VERSION = '/api/v1'
app = Flask(__name__)


@app.route('/tasks/schedule', methods=['GET'])
def schedule():
    """
    Invoked by Cron scheduler (see cron.yaml).
    Schedules all defined policies for evaluation.
    Returns:

    """
    logging.debug('GET /tasks/schedule started...')

    keys = PolicyModel.query().fetch(keys_only=True)
    logging.info('Found %s policies', len(keys))

    for key in keys:
        logging.info('Creating policy_checker deferred task for policy %s', key.id())
        deferred.defer(schedule_tasks.policy_checker, key.id())

    logging.debug('GET /tasks/schedule ended')
    return 'ok', 200


@app.route('/tasks/change_state', methods=['GET'])
def change_state():
    """
    Invoked by policy_tasks.policy_checker().
    Initiate change state.
    Returns:

    """
    logging.debug('GET /tasks/change_state started...')

    policy = request.args['policy']
    state = request.args['state']

    logging.info('Change state requested for policy: \'%s\', state: \'%s\'', policy, state)
    policy_tasks.change_state(policy, state)

    logging.debug('GET /tasks/change_state ended')
    return 'ok', 200


@app.route(API_VERSION + '/time_zones', methods=['GET'])
def time_zones():
    """
    Get all time zones.
    :return: all time zone in the world wide world.
    """
    return json.dumps({'Timezones': tz.get_all_timezones()})


@app.route(API_VERSION + '/add_schedule', methods=['POST'])
def add_schedule():
    """
    Add a schedule.
    Returns:

    """
    schedules_model = SchedulesModel()
    schedules_model.Schedule = {
        'dtype': request.json['dtype'],
        'Corder': request.json['Corder'],
        'Shape': request.json['Shape'],
        '__ndarray__': request.json['__ndarray__']
    }

    schedules_model.Name = request.json['name']
    schedules_model.Timezone = request.json['timezone']
    schedules_model.key = ndb.Key('SchedulesModel', request.json['name'])
    schedules_model.put()
    return 'ok', 200


@app.route(API_VERSION + '/get_schedule', methods=['GET'])
def get_schedule():
    """
    Get a schedule.
    Returns: schedule json

    """
    name = request.args.get('schedule')
    res = SchedulesModel.query(SchedulesModel.Name == name).get()
    if not res:
        return 'not found', 404
    schedule = {}
    schedule.update({'name': res.Name})
    schedule.update(res.Schedule)
    schedule.update({'timezone': res.Timezone})
    logging.debug(json.dumps(res.Schedule))
    return json.dumps(schedule)


@app.route(API_VERSION + '/list_schedules', methods=['GET'])
def list_schedules():
    """
    Get all schedules.
    Returns: A list of schedules

    """
    keys = SchedulesModel.query().fetch(keys_only=True)
    schedules_list = []
    for key in keys:
        schedules_list.append(key.id())
    return json.dumps(schedules_list)


@app.route(API_VERSION + '/del_schedule', methods=['GET'])
def del_schedule():
    """
    Delete a schedule.
    Returns:

    """
    name = request.args.get('schedule')
    res = SchedulesModel.query(SchedulesModel.Name == name).get()
    if not res:
        return 'not found', 404
    policy = PolicyModel.query(PolicyModel.Schedule == name).get()
    if policy:
        return 'Forbidden policy {} is using the schedule'.format(
            policy.Name), 403
    res.key.delete()
    return 'ok', 200


@app.route(API_VERSION + '/add_policy', methods=['POST'])
def add_policy():
    """
    Add policy.
    Returns:

    """
    logging.debug(json.dumps(request.json))
    name = request.json['name']
    projects = request.json['projects']
    clusters = request.json['clusters']
    nodePools = request.json['nodePools']
    schedule_name = request.json['schedulename']

    res = SchedulesModel.query(SchedulesModel.Name == schedule_name).get()
    if not res:
        return 'Schedule \'{}\' not found'.format(schedule_name), 404

    policy_model = PolicyModel()
    policy_model.Name = name
    policy_model.Projects = projects
    policy_model.Clusters = clusters
    policy_model.NodePools = nodePools
    policy_model.Schedule = schedule_name
    policy_model.key = ndb.Key('PolicyModel', name)
    policy_model.put()
    return 'ok', 200


@app.route(API_VERSION + '/get_policy', methods=['GET'])
def get_policy():
    """
    Get policy.
    Returns: policy json

    """
    name = request.args.get('policy')
    res = PolicyModel.query(PolicyModel.Name == name).get()
    logging.debug(res)
    if not res:
        return 'not found', 404
    policy = {}
    policy.update({'name': res.Name})
    policy.update({'projects': res.Projects})
    policy.update({'clusters': res.Clusters})
    policy.update({'nodePools': res.NodePools})
    policy.update({'schedulename': res.Schedule})
    return json.dumps(policy)


@app.route(API_VERSION + '/list_policies', methods=['GET'])
def list_policies():
    """
    Get all polices.
    Returns: List of policies

    """
    keys = PolicyModel.query().fetch(keys_only=True)
    policies_list = []
    for key in keys:
        policies_list.append(key.id())
    return json.dumps(policies_list)


@app.route(API_VERSION + '/del_policy', methods=['GET'])
def del_policy():
    """
    Delete a policy
    Returns:

    """
    name = request.args.get('policy')
    res = PolicyModel.query(PolicyModel.Name == name).get()
    if not res:
        return 'not found', 404
    res.key.delete()
    return 'ok', 200


@app.route('/')
def index():
    """
    Main Page
    :return:
    """
    return 'ok', 200


if __name__ == '__main__':
    app.run(debug=True)
