"""DB model for policy."""
from google.appengine.ext import ndb


class PolicyModel(ndb.Model):
    """
    Class that represents a policy and its associated schedule.
    """

    Name = ndb.StringProperty(indexed=True, required=True)
    Projects = ndb.JsonProperty(repeated=True)
    Clusters = ndb.JsonProperty(repeated=True)
    NodePools = ndb.JsonProperty(repeated=True)
    Schedule = ndb.StringProperty(indexed=True, required=True, repeated=False)
    State = ndb.IntegerProperty(indexed=False, repeated=False)