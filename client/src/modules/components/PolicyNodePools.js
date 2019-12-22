import React from 'react';
import PropTypes from 'prop-types';

// Material UI
import { withStyles } from '@material-ui/core/styles';
import TextField from '@material-ui/core/TextField';
import FormGroup from '@material-ui/core/FormGroup';
import Button from '@material-ui/core/Button';
import IconButton from '@material-ui/core/IconButton';
import ClearIcon from '@material-ui/icons/Clear';

// Lodash
import map from 'lodash/map';
import forOwn from 'lodash/forOwn';

const TEXT_FIELD_WIDTH = 250;

const styles = theme => ({
  root: {
    marginBottom: theme.spacing.unit * 3,
  },
  textField: {
    width: TEXT_FIELD_WIDTH,
    marginRight: theme.spacing.unit,
    marginBottom: theme.spacing.unit,
  },
  iconButton: {
    width: 32,
    height: 32,
  },
  addButton: {
    width: TEXT_FIELD_WIDTH * 2 + theme.spacing.unit,
  },
  sizeSmallButton: {
    padding: 0,
    minHeight: 24,
  },
});

class PolicyNodePools extends React.Component {
  constructor(props, context) {
    super(props, context);
    this.state = {
      nodePools: [
        {
          name: '',
          size: '',
        },
      ],
    };
  }

  componentDidMount() {
    if (this.props.nodePools && this.props.nodePools.length > 0) {
      let nodePools = [];
      this.props.nodePools.forEach(nodePool => {
        forOwn(nodePool, (size, name) => {
          nodePools.push({
            name,
            size,
          });
        });
      });
      this.setState({
        nodePools,
      });
    }
  }

  publishChanges = shouldUpdateErrors => {
    const nodePools = map(this.state.nodePools, nodePool => ({
      [nodePool.name]: nodePool.size,
    }));
    this.props.onChange(nodePools, shouldUpdateErrors);
  };

  handleChange = (index, name) => event => {
    const nodePools = this.state.nodePools.slice();
    nodePools[index][name] = event.target.value;
    this.setState({ nodePools }, () => this.publishChanges(false));
  };

  handleClearNodePool = index => event => {
    const nodePools = this.state.nodePools.slice();
    if (nodePools.length > 1) {
      nodePools.splice(index, 1);
      this.setState({ nodePools }, () => this.publishChanges(true));
    }
  };

  handleAddNodePool = event => {
    const nodePools = this.state.nodePools.slice();
    nodePools.push({
      name: '',
      size: '',
    });
    this.setState({ nodePools }, () => this.publishChanges(false));
  };

  render() {
    const { classes, error } = this.props;
    const { nodePools } = this.state;

    return (
      <div className={classes.root}>
        {map(nodePools, (nodePool, index) => (
          <FormGroup row key={index}>
            <TextField
              id="policy-node-pool-name"
              error={error[index] && error[index][0]}
              helperText=""
              placeholder="name"
              className={classes.textField}
              value={nodePool.name}
              onChange={this.handleChange(index, 'name')}
              margin="none"
            />
            <TextField
              id="policy-node-pool-size"
              error={error[index] && error[index][1]}
              helperText=""
              placeholder="Size"
              className={classes.textField}
              value={nodePool.size}
              onChange={this.handleChange(index, 'size')}
              margin="none"
            />

            {nodePools.length > 1 && (
              <IconButton
                className={classes.iconButton}
                aria-label="Clear"
                onClick={this.handleClearNodePool(index)}
                classes={{
                  root: classes.iconButton,
                }}
              >
                <ClearIcon />
              </IconButton>
            )}
          </FormGroup>
        ))}

        {nodePools.length < 7 && (
          <Button
            variant="outlined"
            color="primary"
            size="small"
            className={classes.addButton}
            onClick={this.handleAddNodePool}
            classes={{
              sizeSmall: classes.sizeSmallButton,
            }}
          >
            Add node pool
          </Button>
        )}
      </div>
    );
  }
}
PolicyNodePools.propTypes = {
  classes: PropTypes.object.isRequired,
  onChange: PropTypes.func.isRequired,
  error: PropTypes.array.isRequired,
};

export default withStyles(styles)(PolicyNodePools);
