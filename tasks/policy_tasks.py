"""Change a state for all matching instances in a project."""
import logging

from model.policymodel import PolicyModel
from gcp.gke import Gke

def change_state(policy_name, state):
    """
    Change a state for a policy.
    Args:
        policy_name: policy name
        state: stop 0 start 1

    """

    # retrive policy model
    logging.debug('Retrieving policy \'%s\'', policy_name)
    policy = PolicyModel.query(PolicyModel.Name == policy_name).get()
    if not policy:
        logging.error('Policy %s not found!', policy_name)
        return 'not found', 404
    
    gke = Gke()

    for project in policy.Projects:
        logging.debug("change_state %s state %s", project, state)
        gke.change_state(project, policy.Clusters, policy.NodePools, state)

    policy.State = int(state)
    policy.put()

    return 'ok', 200
