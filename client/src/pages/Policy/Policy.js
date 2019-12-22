import React from 'react';
import PropTypes from 'prop-types';

// Material UI
import { withStyles } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';
import Button from '@material-ui/core/Button';
import ArrowBackIcon from '@material-ui/icons/ArrowBack';
import IconButton from '@material-ui/core/IconButton';
import TextField from '@material-ui/core/TextField';
import InputLabel from '@material-ui/core/InputLabel';
import FormGroup from '@material-ui/core/FormGroup';
import FormControl from '@material-ui/core/FormControl';
import Select from '@material-ui/core/Select';

// Lodash
import map from 'lodash/map';
import find from 'lodash/find';
import forOwn from 'lodash/forOwn';

// Project
import PolicyNodePools from '../../modules/components/PolicyNodePools';
import AppPageContent from '../../modules/components/AppPageContent';
import AppPageActions from '../../modules/components/AppPageActions';
import PolicyService from '../../modules/api/policy';
import ScheduleService from '../../modules/api/schedule';
import { getDefaultPolicy } from '../../modules/utils/policy';

const styles = theme => ({
  root: {
    height: '100%',
  },
  button: {
    marginRight: theme.spacing.unit * 2,
  },
  textField: {
    width: 250,
    marginBottom: theme.spacing.unit * 3,
  },
  formControl: {
    width: 250,
    marginBottom: theme.spacing.unit * 3,
  },
});

class Policy extends React.Component {
  constructor(props, context) {
    super(props, context);
    this.state = {
      policy: null,
      schedules: null,

      nameError: false,
      scheduleError: false,
      projectsError: false,
      clustersError: false,
      nodePoolsError: [],
    };

    this.policyService = new PolicyService();
    this.scheduleService = new ScheduleService();
  }

  async componentDidMount() {
    try {
      const { match } = this.props;
      const schedules = await this.scheduleService.list();
      let policy;
      if (match.params.policy) {
        policy = await this.policyService.get(match.params.policy);
      } else {
        policy = getDefaultPolicy();
        if (schedules && schedules.length) {
          policy.schedulename = schedules[0];
        }
      }
      this.setState({
        policy,
        schedules,
      });
    } catch (ex) {
      console.error(ex);
    }
  }

  handleChange = name => event => {
    const { policy } = this.state;
    policy[name] = event.target.value;
    this.setState({ policy });
  };

  handleChangeNodePools = (nodePools, shouldUpdateErrors) => {
    const { policy } = this.state;
    policy.nodePools = nodePools;
    if (shouldUpdateErrors) {
      const nodePoolsError = this.getNodePoolsError();
      this.setState({ policy, nodePoolsError });
    } else {
      this.setState({ policy });
    }
  };

  handleChangeProjects = event => {
    const { policy } = this.state;
    policy.projects = event.target.value.replace(/\s/g, '').split(',');
    this.setState({
      policy,
    });
  };

  handleChangeClusters = event => {
    const { policy } = this.state;
    policy.clusters = event.target.value.replace(/\s/g, '').split(',');
    this.setState({
      policy,
    });
  };

  getNodePoolsError = () => {
    const { policy } = this.state;
    const poolNameRe = /^[a-z;,][a-z0-9_\-,;]*[a-z0-9;,]$/;
    const poolSizeRe = /^[0-9]+$/;
    let nodePoolsError = [];
    for (let i = 0; i < policy.nodePools.length; i++) {
      nodePoolsError.push([false, false]);
      forOwn(policy.nodePools[i], (size, name) => {
        if (!poolNameRe.test(name)) {
          nodePoolsError[i][0] = true;
        }
        if (!poolSizeRe.test(size)) {
          nodePoolsError[i][1] = true;
        }
      });
    }
    return nodePoolsError;
  };

  handleSubmit = async event => {
    try {
      const { history } = this.props;
      const { policy } = this.state;

      const nameRe = /^[a-zA-Z][\w-]*[a-zA-Z0-9]$/;
      const projectsRe = /^[a-z][a-z0-9-]+[a-z0-9]$/;
      const clustersRe = /^[a-z][a-z0-9-]+[a-z0-9]$/;

      let nameError = false;
      let projectsError = !policy.projects.length;
      let clustersError = !policy.clusters.length;
      const scheduleError = !policy.schedulename;
      const nodePoolsError = this.getNodePoolsError();

      if (!nameRe.test(policy.name)) {
        nameError = true;
      }

      for (let i = 0; i < policy.projects.length && !projectsError; i++) {
        if (!projectsRe.test(policy.projects[i])) {
          projectsError = true;
        }
      }

      for (let i = 0; i < policy.clusters.length && !clustersError; i++) {
        if (!clustersRe.test(policy.clusters[i])) {
          clustersError = true;
        }
      }

      if (
        nameError ||
        projectsError ||
        clustersError ||
        scheduleError ||
        find(nodePoolsError, nodePoolsError => nodePoolsError[0] || nodePoolsError[1])
      ) {
        this.setState({
          nameError,
          scheduleError,
          projectsError,
          clustersError,
          nodePoolsError,
        });
      } else {
        const response = await this.policyService.add(policy);
        console.log(response);
        history.push('/policies/browser');
      }
    } catch (ex) {
      console.error(ex);
    }
  };

  handleRequestCancel = event => {
    const { history } = this.props;
    history.goBack();
  };

  render() {
    const { classes, edit } = this.props;
    const {
      policy,
      schedules,
      nameError,
      scheduleError,
      projectsError,
      clustersError,
      nodePoolsError,
    } = this.state;

    if (policy) {
      return (
        <div className={classes.root}>
          <AppPageActions>
            <IconButton
              color="primary"
              aria-label="Back"
              onClick={this.handleRequestCancel}
            >
              <ArrowBackIcon />
            </IconButton>

            {edit ? (
              <Typography variant="subheading" color="primary">
                Edit policy {policy.name}
              </Typography>
            ) : (
              <Typography variant="subheading" color="primary">
                Create a policy
              </Typography>
            )}
          </AppPageActions>

          <AppPageContent>
            <FormGroup row={false}>
              <TextField
                disabled={edit}
                id="policy-name"
                error={nameError}
                helperText=""
                label="Policy name"
                className={classes.textField}
                value={this.state.policy.name}
                onChange={this.handleChange('name')}
                margin="none"
                autoFocus
                InputLabelProps={{
                  shrink: true,
                }}
              />

              <FormControl className={classes.formControl}>
                <InputLabel
                  shrink
                  error={scheduleError}
                  htmlFor="schedule-input"
                >
                  Schedule name
                </InputLabel>
                <Select
                  error={scheduleError}
                  native
                  value={this.state.policy.schedulename}
                  onChange={this.handleChange('schedulename')}
                  inputProps={{
                    id: 'schedule-input',
                  }}
                >
                  {map(schedules, schedule => (
                    <option key={schedule} value={schedule}>
                      {schedule}
                    </option>
                  ))}
                </Select>
              </FormControl>

              <TextField
                id="projects-list"
                error={projectsError}
                helperText="Separated by comma"
                label="Projects"
                className={classes.textField}
                value={policy.projects.join(',')}
                onChange={this.handleChangeProjects}
                margin="none"
                InputLabelProps={{
                  shrink: true,
                }}
              />

              <TextField
                id="clusters-list"
                error={clustersError}
                helperText="Separated by comma"
                label="Clusters"
                className={classes.textField}
                value={policy.clusters.join(',')}
                onChange={this.handleChangeClusters}
                margin="none"
                InputLabelProps={{
                  shrink: true,
                }}
              />

              <PolicyNodePools
                error={nodePoolsError}
                nodePools={policy.nodePools}
                onChange={this.handleChangeNodePools}
              />
            </FormGroup>

            <Button
              className={classes.button}
              variant="contained"
              color="primary"
              size="small"
              onClick={this.handleSubmit}
            >
              Save
            </Button>
            <Button
              className={classes.button}
              variant="outlined"
              color="primary"
              size="small"
              onClick={this.handleRequestCancel}
            >
              Cancel
            </Button>
          </AppPageContent>
        </div>
      );
    } else {
      return <div />;
    }
  }
}

Policy.propTypes = {
  classes: PropTypes.object.isRequired,
};

export default withStyles(styles)(Policy);
