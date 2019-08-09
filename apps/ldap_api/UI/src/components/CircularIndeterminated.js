import React from 'react';
import PropTypes from 'prop-types';
import { withStyles } from '@material-ui/core/styles';
import CircularProgress from '@material-ui/core/CircularProgress';

const styles = theme => ({
  root: {
    textAlign: 'center'
  },
  progress: {
    margin: theme.spacing.unit * 2,
  },
});

function CircularIndeterminated(props) {
  const { classes } = props;
  return (
    <div className={classes.root}>
      <CircularProgress className={classes.progress} />
    </div>
  );
}

CircularIndeterminated.propTypes = {
  classes: PropTypes.object.isRequired,
};

export default withStyles(styles)(CircularIndeterminated);