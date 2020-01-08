"""Interactions with GKE."""

import logging

import backoff
from google.auth import app_engine
from googleapiclient import discovery
from googleapiclient.errors import HttpError
from google.appengine.ext import ndb
from util import gcp, utils
from model.gkenoodespoolsmodel import GkeNodePoolModel

SCOPES = ['https://www.googleapis.com/auth/cloud-platform']

CREDENTIALS = app_engine.Credentials(scopes=SCOPES)


class Gke(object):
    """GKE engine actions."""


    def __init__(self):
        self.gke = discovery.build('container', 'v1')


    def change_state(self, project, clusters, node_pools, state):
        logging.info('Chaning to state \'%s\', project \'%s\', clusters \'%s\', node pools \'%s\'', state, project, clusters, node_pools)

        # convert list of dictionaries into a dict for easier work
        node_pools = {k:v for element in node_pools for k,v in element.items()}

        try:
            project_clusters = self.list_clusters(project)

            # iterate over all clusters for the project
            for cluster in project_clusters:
                cluster_name = cluster['name']

                # skip over not included clusters
                if cluster_name not in clusters:
                    logging.debug('Skipping cluster \'%s\' as it is not included in the policy', cluster_name)
                    continue

                logging.info('Handling cluster \'%s\' of project \'%s\'', cluster_name, project)

                # iterate over all node pools of the cluster
                cluster_node_pools = cluster['nodePools']
                for node_pool in cluster_node_pools:
                    node_pool_name = node_pool['name']

                    # skip over not included node pools
                    if node_pool_name not in node_pools:
                        logging.debug('Skipping cluster\'s \'%s\' node pool \'%s\' as it is not included in the policy', cluster_name, node_pool_name)
                        continue

                    logging.info('Handling node pool \'%s\' of cluster \'%s\' of project \'%s\'', node_pool_name, cluster_name, project)

                    # handle autoscaling node-pools differently
                    if 'autoscaling' in node_pool and node_pool['autoscaling']['enabled']:

                        name = node_pool['selfLink'][node_pool['selfLink'].find('/projects/') + 1:]
                        logging.info('Node pool \'%s\' is configured with autoscaling', name)

                        current_autoscaling = node_pool['autoscaling']

                        autoscaling = {
                            'autoscaling': {
                                'enabled': current_autoscaling['enabled'],
                                'minNodeCount': current_autoscaling['minNodeCount'],
                                'maxNodeCount': current_autoscaling['maxNodeCount'],
                                'autoprovisioned': current_autoscaling['autoprovisioned'] if 'autoprovisioned' in current_autoscaling else False
                            }
                        }

                        # set new size
                        if int(state) == 1: # size up
                            # retrieve the previously stored model
                            model = GkeNodePoolModel.query(GkeNodePoolModel.Name == name).get()
                            if not model:
                                logging.warn('No node pool model found in db for name \'%s\'', name)
                                continue

                            # get the up size from the model
                            autoscaling['autoscaling']['maxNodeCount'] = model.NumberOfNodes

                            # update the max node count of the node-pool
                            self.gke.projects().locations().clusters().nodePools().setAutoscaling(name=name, body=autoscaling).execute()
                            logging.info('Sized up node pool \'%s\' of cluster \'%s\' in project \'%s\' to \'%s\' nodes', node_pool_name, cluster_name, project, autoscaling['autoscaling']['maxNodeCount'])

                            # delete the stored model
                            model.key.delete()
                            logging.debug('Deleted node pool model for node pool name \'%s\'', name)
                        
                        else: # size down

                            # save current number of nodes for later restore
                            model = GkeNodePoolModel()
                            model.Name = name
                            model.NumberOfNodes = autoscaling['autoscaling']['maxNodeCount']
                            model.key = ndb.Key('GkeNodePoolModel', name)
                            model.put()
                            logging.debug('Saved node pool model for node pool name \'%s\' with \'%s\' number of nodes', name, autoscaling['autoscaling']['maxNodeCount'])

                            # find out the down size value for the node pool
                            autoscaling['autoscaling']['maxNodeCount'] = node_pools[node_pool_name]

                            # do actual resize
                            self.gke.projects().locations().clusters().nodePools().setAutoscaling(name=name, body=autoscaling).execute()
                            logging.info('Sized down node pool \'%s\' of cluster \'%s\' in project \'%s\' to \'%s\' nodes', node_pool_name, cluster_name, project, autoscaling['autoscaling']['maxNodeCount'])

                    else: # node pool autoscaling is not turned on, changing managed instance group configuration

                        # iterate over all instance group urls of the node pool
                        for instance_group_url in node_pool['instanceGroupUrls']:

                            logging.info('Handling instance group url \'%s\' of node pool \'%s\' of cluster \'%s\'', instance_group_url, node_pool_name, cluster_name)

                            # grab the current number of nodes in the instance group
                            number_of_nodes = gcp.get_instancegroup_no_of_nodes_from_url(instance_group_url)
                            logging.info('Current number of nodes is \'%s\' for node pool \'%s\' of cluster \'%s\' in project \'%s\'', number_of_nodes, node_pool_name, cluster_name, project)

                            # do resizing
                            if int(state) == 1: # size up

                                # retrieve the previously stored model
                                model = GkeNodePoolModel.query(GkeNodePoolModel.Name == instance_group_url).get()
                                if not model:
                                    logging.warn('No node pool model found in db for instance group url \'%s\'', instance_group_url)
                                    continue

                                # get the up size from the model
                                new_size = model.NumberOfNodes

                                gcp.resize_node_pool(new_size, instance_group_url)
                                logging.info('Sized up node pool \'%s\' of cluster \'%s\' in project \'%s\' to \'%s\' nodes', node_pool_name, cluster_name, project, new_size)

                                # delete the stored model
                                model.key.delete()
                                logging.debug('Deleted node pool model for instance group url \'%s\'', instance_group_url)

                            else: # size down

                                # save current number of nodes for later restore
                                model = GkeNodePoolModel()
                                model.Name = instance_group_url
                                model.NumberOfNodes = number_of_nodes
                                model.key = ndb.Key('GkeNodePoolModel', instance_group_url)
                                model.put()
                                logging.debug('Saved node pool model for instance group url \'%s\' with \'%s\' number of nodes', instance_group_url, number_of_nodes)

                                # find out the down size value for the node pool
                                new_size = node_pools[node_pool_name]

                                # do actual resize
                                gcp.resize_node_pool(new_size, instance_group_url)
                                logging.info('Sized down node pool \'%s\' of cluster \'%s\' in project \'%s\' to \'%s\' nodes', node_pool_name, cluster_name, project, new_size)

        except HttpError as http_error:
            logging.error(http_error)
            return 'Error', 500
        return 'ok', 200


    @backoff.on_exception(
        backoff.expo, HttpError, max_tries=8, giveup=utils.fatal_code)
    def list_clusters(self, project):
        """
        List all clusters within the project
        Args:
            project: project

        """
        logging.info('Listing all GKE clusters for project \'%s\'...', project)
        parent = 'projects/%s/locations/-' % project
        result = self.gke.projects().locations().clusters().list(parent=parent).execute()
        
        clusters = []
        if 'clusters' in result:
            clusters = result['clusters']

        logging.info('Found %s clusters in project \'%s\'', len(clusters), project)
        logging.debug('Clusters in project \'%s\': %s', project, clusters)

        return clusters