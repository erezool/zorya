"""Check if there is a need to take an action for a policy."""
import logging

from google.appengine.api import taskqueue

import numpy as np
from model.policymodel import PolicyModel
from model.schedulesmodel import SchedulesModel
from util import tz, utils

def policy_checker(name):
    """
    Checks a policy if state change needed and triggers a state chnage if so
    Args:
        name: policy name
    """
    # retrieve policy model
    logging.debug('Retrieving policy %s', name)
    policy = PolicyModel.query(PolicyModel.Name == name).get()
    if not policy:
        logging.error('Policy %s not found!', name)
        return 'not found', 404
    
    # retrieve schedule model
    logging.debug('Retrieving schedule %s', policy.Schedule)
    schedule = SchedulesModel.query(SchedulesModel.Name == policy.Schedule).get()
    if not schedule:
        logging.error('Schedule %s not found!', policy.Schedule)
        return 'not found', 404
    
    # calc current day and hour of the schedule and retrive its requested state
    time_at_zone = tz.get_time_at_timezone(schedule.Timezone)
    logging.debug('Time at Timezone \'%s\' is \'%s\'', schedule.Timezone, time_at_zone)
    day, hour = tz.convert_time_to_index(time_at_zone)
    logging.debug('Timezone\'s day: \'%s\' hour: \'%s\'', day, hour)
    arr = np.asarray(schedule.Schedule['__ndarray__'], dtype=np.int).flatten()
    scheduled_state = arr[day * 24 + hour]
    logging.info('Scheduled state of schedule \'%s\' for day \'%s\' and hour \'%s\' is: \'%s\'', schedule.Name, day, hour, scheduled_state)

    # execute change state if needed
    logging.info('Needed state: \'%s\', Last state: \'%s\'', scheduled_state, policy.State)
    if scheduled_state != policy.State:
        task = taskqueue.add(queue_name='zorya-tasks',
                                url="/tasks/change_state",
                                method='GET',
                                params={
                                    'policy': name,
                                    'state': scheduled_state
                                },
                            )
        logging.info('Policy \'%s\' change_state to \'%s\' task \'%s\' enqueued with ETA \'%s\'', name, scheduled_state, task.name, task.eta)
    else:
        logging.info('No change_state needed for policy \'%s\'', name)
    
    return 'ok', 200
