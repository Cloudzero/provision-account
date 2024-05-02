# Initial Image for a Rolling Update of the agent.

Kebernetes has a concept of rolling updates to enable new version of Pod (image)
to be updates one node at a time.  This is great when updating from one version to the next.

The downside, is that the intiial update will mass deploy to all nodes at once. This might be ok but not ok depending on the user situation.
A strategy is to intitally deploy an image that does nothing putting the least amount of load on a system.  Then use the power of kubernetes rolling
update to deploy the required version one node at a time.

This Directory build image 0.0.0 or the cloudzero/cloudwatch-agent.
